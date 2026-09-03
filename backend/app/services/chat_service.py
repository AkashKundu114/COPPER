import re
import time
from collections.abc import AsyncGenerator

from sqlalchemy.orm import Session

from app.ai.agents.automation_agent import automation_agent
from app.ai.agents.coding_agent import coding_agent
from app.ai.agents.document_agent import document_agent
from app.ai.agents.image_agent import image_agent
from app.ai.agents.reminder_agent import reminder_agent
from app.ai.agents.research_agent import research_agent
from app.ai.agents.vision_agent import vision_agent
from app.ai.llm.model_manager import model_manager
from app.ai.llm.prompt_manager import build_messages, get_mode_prompt, get_system_prompt
from app.ai.memory.context_engine import context_engine
from app.ai.memory.memory_manager import memory_manager
from app.ai.memory.persistent_memory import persistent_memory
from app.ai.orchestration.agent_router import is_consequential_action, route_message_detailed
from app.ai.orchestration.langchain_manager import langchain_manager
from app.ai.orchestration.planner import nexus_planner
from app.ai.orchestration.task_graph import task_graph_executor
from app.core.constants import AgentType, LLMProvider
from app.core.guardian import DisagreementLevel
from app.core.logger import logger
from app.services.directive_service import directive_service
from app.services.guardian_service import guardian_service
from app.services.self_model_service import self_model_service

AGENT_MAP = {
    AgentType.CODING: coding_agent,
    AgentType.DOCUMENT: document_agent,
    AgentType.AUTOMATION: automation_agent,
    AgentType.REMINDER: reminder_agent,
    AgentType.RESEARCH: research_agent,
    AgentType.VISION: vision_agent,
    AgentType.IMAGE: image_agent,
}


class ChatService:
    def _resolve_chat_model(self, agent_type: AgentType, message: str, agent=None) -> str:
        """
        Determines the target model tag:
        1. Agent-specified model if specialized agent is active.
        2. Explicit user preference saved in persistent_memory.
        3. Adaptive Intent: Fast reflex mini-model for simple greetings, identity, and personal facts.
        4. Manifest default (8B tier).
        """
        if agent and hasattr(agent, "get_target_model"):
            return agent.get_target_model()

        preferred_model = persistent_memory.get_chat_model()
        if preferred_model:
            return preferred_model

        msg_clean = message.strip().lower()
        simple_patterns = [
            r"^(hi|hello|hey|greetings|howdy|sup)\b",
            r"\b(who am i|whats my name|what is my name|what do i do)\b",
            r"\b(whats my age|what is my age|how old am i|my age)\b",
            r"\b(tell me a joke|fun thought|who are you|what can you do)\b",
            r"\b(what time is it|current date|today's date)\b",
        ]
        if any(re.search(pat, msg_clean) for pat in simple_patterns):
            return model_manager.get_mini_model(prefer_tag=True)

        return model_manager.get_model("core_agents.chat", "llama3.1:8b")

    async def process_message(
        self,
        session_id: str,
        message: str,
        provider: LLMProvider = LLMProvider.OLLAMA,
        stream: bool = False,
        db: Session | None = None,
    ) -> dict:
        # Check Operator Directives (model switching, cognitive mode, voice, VRAM)
        directive_res = await directive_service.evaluate(message, session_id=session_id)
        prefix_confirmation = ""
        if directive_res.is_directive:
            if not directive_res.remaining_prompt:
                await context_engine.append_message(session_id, "user", message)
                await context_engine.append_message(session_id, "assistant", directive_res.confirmation, agent_type="directive")
                return {
                    "response": directive_res.confirmation,
                    "agent_type": "directive",
                    "session_id": session_id,
                    "metrics": {
                        "model": "system:directive-engine",
                        "prompt_tokens": max(1, len(message.split())),
                        "completion_tokens": max(1, len(directive_res.confirmation.split())),
                        "total_tokens": max(2, len(message.split()) + len(directive_res.confirmation.split())),
                        "tokens_per_sec": 100.0,
                        "ttft_ms": 5.0,
                        "total_time_sec": 0.05,
                        "total_time_ms": 50.0,
                    },
                }
            prefix_confirmation = directive_res.confirmation + "\n\n---\n\n"
            message = directive_res.remaining_prompt

        routing_res = await route_message_detailed(message)
        agent_type = routing_res.agent

        if db is not None and is_consequential_action(message):
            verdict = await guardian_service.evaluate_action(
                proposed_action=message,
                context=self._build_guardian_context(message, agent_type),
                db=db,
                session_id=session_id,
                actor=str(agent_type),
            )
            if verdict.level >= DisagreementLevel.CHALLENGE:
                from app.core.guardian import guardian_engine

                challenge_text = guardian_engine.format_challenge(verdict)
                return {
                    "response": challenge_text,
                    "agent_type": agent_type,
                    "session_id": session_id,
                    "guardian_verdict": verdict.to_dict(),
                }

        history, memory_context, self_context = await context_engine.build_context(session_id, message)
        await context_engine.append_message(session_id, "user", message)

        # NEXUS Multi-Agent Collaboration Check
        if nexus_planner.should_consider_decomposition(message, router_confidence=routing_res.confidence):
            try:
                plan = await nexus_planner.plan(message, memory_context)
                if plan.is_decomposition:
                    logger.info(f"NEXUS decomposed task into {len(plan.tasks)} sub-tasks: {plan.goal}")

                    async def ws_graph_event(event_type: str, payload: dict):
                        from app.api.websocket.manager import manager

                        await manager.send_task_graph_update(session_id, event_type, payload)

                    graph_result = await task_graph_executor.execute_plan(
                        plan, memory_context=memory_context, session_id=session_id, on_event=ws_graph_event
                    )

                    await context_engine.append_message(
                        session_id, "assistant", graph_result.final_response, agent_type="nexus_multi_agent"
                    )
                    await memory_manager.save_interaction(
                        session_id, message, graph_result.final_response, "nexus_multi_agent"
                    )

                    final_resp = prefix_confirmation + graph_result.final_response if prefix_confirmation else graph_result.final_response
                    return {
                        "response": final_resp,
                        "agent_type": "nexus_multi_agent",
                        "session_id": session_id,
                        "task_graph": graph_result.to_dict(),
                    }
            except Exception as plan_err:
                logger.warning(f"NEXUS decomposition fallback to single agent: {plan_err}")

        agent = AGENT_MAP.get(agent_type)
        t_start = time.perf_counter()
        ollama_metrics: dict = {}
        target_model = self._resolve_chat_model(agent_type, message, agent=agent)
        try:
            if agent:
                response = await agent.run(message, history, memory_context, provider, session_id=session_id)
            else:
                system = get_system_prompt(AgentType.CHAT, memory_context, self_context)
                messages = build_messages(system, history, message)
                response = await langchain_manager.ainvoke(
                    messages, provider, model=target_model, metrics_collector=ollama_metrics
                )
            if prefix_confirmation:
                response = prefix_confirmation + response
            t_end = time.perf_counter()

            prompt_tokens = ollama_metrics.get("prompt_eval_count") or max(1, int(len(message.split()) * 1.3))
            completion_tokens = ollama_metrics.get("eval_count") or max(1, int(len(response.split()) * 1.3))
            total_tokens = prompt_tokens + completion_tokens
            total_time_sec = round(t_end - t_start, 2)
            total_time_ms = round((t_end - t_start) * 1000, 1)
            ttft_ms = round(total_time_ms * 0.2, 1)
            tokens_per_sec = round(completion_tokens / max(0.001, total_time_sec), 1)
            model_selected = ollama_metrics.get("model") or target_model

            metrics = {
                "model": model_selected,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "tokens_per_sec": tokens_per_sec,
                "ttft_ms": ttft_ms,
                "total_time_sec": total_time_sec,
                "total_time_ms": total_time_ms,
                "confidence": round(routing_res.confidence, 2) if (routing_res and hasattr(routing_res, "confidence")) else 0.95,
            }

            await context_engine.append_message(
                session_id,
                "assistant",
                response,
                agent_type=agent_type,
                model_name=model_selected,
                latency_ms=total_time_ms,
            )
            await memory_manager.save_interaction(session_id, message, response, agent_type)

            # Record to system telemetry
            try:
                from app.api.routes.system import record_token_usage

                record_token_usage(prompt_tokens, completion_tokens, total_time_sec)
            except Exception:
                pass

            # Send correction acknowledgment if user corrected COPPER
            if self_model_service.detect_correction(message):
                try:
                    from app.api.websocket.manager import manager

                    recent = self_model_service.get_all(category="correction", limit=1)
                    entry = recent[0] if recent else {"id": "", "content": message[:150]}
                    await manager.send_correction_ack(session_id, entry)
                except Exception:
                    pass

            return {
                "response": response,
                "agent_type": agent_type,
                "session_id": session_id,
                "metrics": metrics,
            }
        except Exception as e:
            logger.error(f"Chat service error: {e}")
            raise

    async def stream_message(
        self,
        session_id: str,
        message: str,
        provider: LLMProvider = LLMProvider.OLLAMA,
        mode: str = "auto",
        metrics_collector: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        # Check Operator Directives (model switching, cognitive mode, voice, VRAM)
        directive_res = await directive_service.evaluate(message, session_id=session_id)
        if directive_res.is_directive:
            if "cognitive_mode" in directive_res.updates:
                mode = directive_res.updates["cognitive_mode"]

            try:
                from app.api.websocket.manager import manager

                await manager.send(
                    session_id,
                    {
                        "type": "preference_update",
                        "updates": directive_res.updates,
                    },
                )
            except Exception:
                pass

            yield directive_res.confirmation
            if not directive_res.remaining_prompt:
                if metrics_collector is not None:
                    metrics_collector.update({
                        "model": "system:directive-engine",
                        "prompt_tokens": max(1, len(message.split())),
                        "completion_tokens": max(1, len(directive_res.confirmation.split())),
                        "total_tokens": max(2, len(message.split()) + len(directive_res.confirmation.split())),
                        "tokens_per_sec": 100.0,
                        "ttft_ms": 10.0,
                        "total_time_sec": 0.05,
                        "total_time_ms": 50.0,
                    })
                await context_engine.append_message(session_id, "user", message)
                await context_engine.append_message(
                    session_id, "assistant", directive_res.confirmation, agent_type="directive"
                )
                return

            yield "\n\n---\n\n"
            message = directive_res.remaining_prompt

        routing_res = await route_message_detailed(message)
        agent_type = routing_res.agent
        history, memory_context, self_context = await context_engine.build_context(session_id, message)
        await context_engine.append_message(session_id, "user", message)
        agent = AGENT_MAP.get(agent_type)

        t_start = time.perf_counter()
        first_token_time = None
        full_response = []
        ollama_metrics: dict = {}

        # Check NEXUS Multi-Agent Collaboration
        if mode == "auto" and nexus_planner.should_consider_decomposition(
            message, router_confidence=routing_res.confidence
        ):
            try:
                yield "🧠 *NEXUS Planner evaluating multi-agent workflow decomposition...*\n\n"
                first_token_time = time.perf_counter()
                plan = await nexus_planner.plan(message, memory_context)
                if plan.is_decomposition:
                    yield f"📋 **NEXUS Multi-Agent Execution Plan ({len(plan.tasks)} tasks):**\n"
                    for t in plan.tasks:
                        deps = f" *(depends on: {', '.join(t.depends_on)})*" if t.depends_on else " *(parallel)*"
                        yield f"- **{t.id} [{t.agent}]:** {t.instruction}{deps}\n"
                    yield "\n🚀 *Executing Multi-Agent DAG in Parallel...*\n\n"

                    async def ws_graph_event(event_type: str, payload: dict):
                        from app.api.websocket.manager import manager

                        await manager.send_task_graph_update(session_id, event_type, payload)

                    graph_result = await task_graph_executor.execute_plan(
                        plan, memory_context=memory_context, session_id=session_id, on_event=ws_graph_event
                    )

                    yield "🎯 **Final Synthesis Response:**\n\n"
                    yield graph_result.final_response

                    t_end = time.perf_counter()
                    total_time_sec = round(t_end - t_start, 2)
                    ttft_ms = round((first_token_time - t_start) * 1000, 1) if first_token_time else 150.0
                    prompt_tokens = max(1, int(len(message.split()) * 1.3) + (len(plan.tasks) * 50))
                    completion_tokens = max(1, int(len(graph_result.final_response.split()) * 1.3))
                    total_tokens = prompt_tokens + completion_tokens
                    tokens_per_sec = round(completion_tokens / max(0.001, total_time_sec), 1)

                    if metrics_collector is not None:
                        metrics_collector.update({
                            "model": "nexus:multi-agent-dag",
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": total_tokens,
                            "tokens_per_sec": tokens_per_sec,
                            "ttft_ms": ttft_ms,
                            "total_time_sec": total_time_sec,
                            "total_time_ms": round((t_end - t_start) * 1000, 1),
                        })

                    await context_engine.append_message(
                        session_id, "assistant", graph_result.final_response, agent_type="nexus_multi_agent"
                    )
                    await memory_manager.save_interaction(
                        session_id, message, graph_result.final_response, "nexus_multi_agent"
                    )
                    return
            except Exception as nexus_err:
                logger.warning(f"NEXUS streaming planning fallback: {nexus_err}")

        try:
            from app.ai.llm.model_manager import model_manager

            if mode == "reasoning":
                model_name = model_manager.get_model("core_agents.reasoning", "deepseek-r1-abliterated:7b")
                system = get_mode_prompt(mode, memory_context, self_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(
                    messages, provider, model=model_name, metrics_collector=ollama_metrics
                )
            elif mode == "coding":
                model_name = model_manager.get_model("core_agents.coding", "qwen2.5-coder-abliterated:7b")
                system = get_mode_prompt(mode, memory_context, self_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(
                    messages, provider, model=model_name, metrics_collector=ollama_metrics
                )
            elif mode == "document":
                model_name = model_manager.get_document_model()
                system = get_mode_prompt(mode, memory_context, self_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(
                    messages, provider, model=model_name, metrics_collector=ollama_metrics
                )
            elif mode == "research":
                model_name = model_manager.get_model("core_agents.reasoning", "mistral-abliterated:7b")
                system = get_mode_prompt(mode, memory_context, self_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(
                    messages, provider, model=model_name, metrics_collector=ollama_metrics
                )
            elif mode == "fast":
                model_name = model_manager.get_mini_model()
                system = get_mode_prompt(mode, memory_context, self_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(
                    messages, provider, model=model_name, metrics_collector=ollama_metrics
                )
            elif agent and hasattr(agent, "stream"):
                model_name = self._resolve_chat_model(agent_type, message, agent=agent)
                gen = agent.stream(message, history, memory_context, provider, metrics_collector=ollama_metrics, session_id=session_id)
            else:
                model_name = self._resolve_chat_model(agent_type, message, agent=agent)
                system = get_mode_prompt("auto", memory_context, self_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(
                    messages, provider, model=model_name, metrics_collector=ollama_metrics
                )

            async for chunk in gen:
                if first_token_time is None and chunk.strip():
                    first_token_time = time.perf_counter()
                full_response.append(chunk)
                yield chunk
            t_end = time.perf_counter()
            complete = "".join(full_response)

            # Compute detailed token & latency telemetry
            ttft_ms = round((first_token_time - t_start) * 1000, 1) if first_token_time else round((t_end - t_start) * 1000, 1)
            total_time_sec = round(t_end - t_start, 2)
            total_time_ms = round((t_end - t_start) * 1000, 1)

            prompt_tokens = ollama_metrics.get("prompt_eval_count") or max(1, int(len(message.split()) * 1.3))
            completion_tokens = ollama_metrics.get("eval_count") or max(1, int(len(complete.split()) * 1.3))
            total_tokens = prompt_tokens + completion_tokens

            eval_duration_nanos = ollama_metrics.get("eval_duration")
            if eval_duration_nanos:
                eval_sec = eval_duration_nanos / 1e9
                tokens_per_sec = round(completion_tokens / max(0.001, eval_sec), 1)
            else:
                gen_duration_sec = max(0.001, t_end - (first_token_time or t_start))
                tokens_per_sec = round(completion_tokens / gen_duration_sec, 1)

            model_selected = ollama_metrics.get("model") or model_name

            metrics = {
                "model": model_selected,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "tokens_per_sec": tokens_per_sec,
                "ttft_ms": ttft_ms,
                "total_time_sec": total_time_sec,
                "total_time_ms": total_time_ms,
                "confidence": round(routing_res.confidence, 2) if (routing_res and hasattr(routing_res, "confidence")) else 0.95,
            }

            if metrics_collector is not None:
                metrics_collector.update(metrics)

            await context_engine.append_message(
                session_id,
                "assistant",
                complete,
                agent_type=agent_type,
                model_name=model_selected,
                latency_ms=total_time_ms,
            )
            await memory_manager.save_interaction(session_id, message, complete, agent_type)

            # Send correction acknowledgment if user corrected COPPER
            if self_model_service.detect_correction(message):
                try:
                    from app.api.websocket.manager import manager

                    recent = self_model_service.get_all(category="correction", limit=1)
                    entry = recent[0] if recent else {"id": "", "content": message[:150]}
                    await manager.send_correction_ack(session_id, entry)
                except Exception:
                    pass

            # Record genuine token metrics in telemetry service
            try:
                from app.api.routes.system import record_token_usage

                record_token_usage(prompt_tokens, completion_tokens, total_time_sec)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"\n[Error: {e}]"

    async def get_history(self, session_id: str) -> list[dict]:
        return await context_engine.get_history(session_id)

    async def clear_history(self, session_id: str) -> None:
        await context_engine.clear_session(session_id)

    def _build_guardian_context(self, message: str, agent_type: AgentType) -> dict:
        msg_lower = message.lower()
        destructive_markers = ["rm -rf", "format ", "del /f", "dd if=", "mkfs", "wipe", "factory reset"]
        return {
            "is_destructive": agent_type == AgentType.AUTOMATION and any(m in msg_lower for m in destructive_markers)
        }


chat_service = ChatService()
