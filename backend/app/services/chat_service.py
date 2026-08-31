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
from app.ai.llm.prompt_manager import build_messages, get_mode_prompt, get_system_prompt
from app.ai.memory.context_engine import context_engine
from app.ai.memory.memory_manager import memory_manager
from app.ai.orchestration.agent_router import is_consequential_action, route_message, route_message_detailed
from app.ai.orchestration.langchain_manager import langchain_manager
from app.ai.orchestration.planner import nexus_planner
from app.ai.orchestration.task_graph import task_graph_executor
from app.core.constants import AgentType, LLMProvider
from app.core.guardian import DisagreementLevel
from app.core.logger import logger
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
    async def process_message(
        self,
        session_id: str,
        message: str,
        provider: LLMProvider = LLMProvider.OLLAMA,
        stream: bool = False,
        db: Session | None = None,
    ) -> dict:
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

                    await context_engine.append_message(session_id, "assistant", graph_result.final_response)
                    await memory_manager.save_interaction(session_id, message, graph_result.final_response, "nexus_multi_agent")

                    return {
                        "response": graph_result.final_response,
                        "agent_type": "nexus_multi_agent",
                        "session_id": session_id,
                        "task_graph": graph_result.to_dict(),
                    }
            except Exception as plan_err:
                logger.warning(f"NEXUS decomposition fallback to single agent: {plan_err}")

        agent = AGENT_MAP.get(agent_type)
        try:
            if agent:
                response = await agent.run(message, history, memory_context, provider)
            else:
                system = get_system_prompt(AgentType.CHAT, memory_context, self_context)
                messages = build_messages(system, history, message)
                response = await langchain_manager.ainvoke(messages, provider)
            await context_engine.append_message(session_id, "assistant", response)
            await memory_manager.save_interaction(session_id, message, response, agent_type)

            # Send correction acknowledgment if user corrected COPPER
            if self_model_service.detect_correction(message):
                try:
                    from app.api.websocket.manager import manager

                    recent = self_model_service.get_all(category="correction", limit=1)
                    entry = recent[0] if recent else {"id": "", "content": message[:150]}
                    await manager.send_correction_ack(session_id, entry)
                except Exception:
                    pass

            return {"response": response, "agent_type": agent_type, "session_id": session_id}
        except Exception as e:
            logger.error(f"Chat service error: {e}")
            raise

    async def stream_message(
        self, session_id: str, message: str, provider: LLMProvider = LLMProvider.OLLAMA, mode: str = "auto"
    ) -> AsyncGenerator[str, None]:
        routing_res = await route_message_detailed(message)
        agent_type = routing_res.agent
        history, memory_context, self_context = await context_engine.build_context(session_id, message)
        await context_engine.append_message(session_id, "user", message)
        agent = AGENT_MAP.get(agent_type)

        # Intercept unload VRAM requests explicitly before hitting LLMs
        lowered = message.strip().lower()
        if lowered in [
            "unload model",
            "unload models",
            "unload ur pre-loaed model",
            "unload your models",
            "unload pre-loaded model",
            "clear vram",
            "free memory",
            "unload",
        ]:
            from app.ai.llm.ollama_client import ollama_client

            yield "Unloading AI models from GPU VRAM to free system memory...\n\n"
            result = await ollama_client.unload_all_models()
            yield result
            return

        start_time = time.time()
        full_response = []

        # Check NEXUS Multi-Agent Collaboration
        if mode == "auto" and nexus_planner.should_consider_decomposition(message, router_confidence=routing_res.confidence):
            try:
                yield "🧠 *NEXUS Planner evaluating multi-agent workflow decomposition...*\n\n"
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

                    await context_engine.append_message(session_id, "assistant", graph_result.final_response)
                    await memory_manager.save_interaction(session_id, message, graph_result.final_response, "nexus_multi_agent")
                    return
            except Exception as nexus_err:
                logger.warning(f"NEXUS streaming planning fallback: {nexus_err}")

        try:
            from app.ai.llm.model_manager import model_manager

            if mode == "reasoning":
                system = get_mode_prompt(mode, memory_context, self_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(messages, provider, model="deepseek-r1:7b")
            elif mode == "coding":
                system = get_mode_prompt(mode, memory_context, self_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(messages, provider, model="qwen2.5-coder:7b")
            elif mode == "document":
                system = get_mode_prompt(mode, memory_context, self_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(messages, provider, model=model_manager.get_document_model())
            elif mode == "research":
                system = get_mode_prompt(mode, memory_context, self_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(messages, provider, model="mistral:7b")
            elif mode == "fast":
                system = get_mode_prompt(mode, memory_context, self_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(messages, provider, model=model_manager.get_mini_model())
            elif agent and hasattr(agent, "stream"):
                gen = agent.stream(message, history, memory_context, provider)
            else:
                system = get_mode_prompt("auto", memory_context, self_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(messages, provider, model=model_manager.get_mini_model())

            async for chunk in gen:
                full_response.append(chunk)
                yield chunk
            complete = "".join(full_response)
            await context_engine.append_message(session_id, "assistant", complete)
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

            # Record genuine token metrics
            try:
                from app.api.routes.system import record_token_usage

                prompt_toks = max(1, int(len(message.split()) * 1.3))
                comp_toks = max(1, int(len(complete.split()) * 1.3))
                duration = time.time() - start_time
                record_token_usage(prompt_toks, comp_toks, duration)
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
