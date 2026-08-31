import asyncio
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from app.ai.agents.automation_agent import automation_agent
from app.ai.agents.coding_agent import coding_agent
from app.ai.agents.document_agent import document_agent
from app.ai.agents.image_agent import image_agent
from app.ai.agents.reminder_agent import reminder_agent
from app.ai.agents.research_agent import research_agent
from app.ai.agents.vision_agent import vision_agent
from app.ai.orchestration.context_bus import context_bus
from app.ai.orchestration.planner import PlanResult, SubTask
from app.core.forge_sandbox import forge_sandbox
from app.core.logger import logger

AGENT_NAME_MAP = {
    "AXIS": coding_agent,
    "CODING": coding_agent,
    "FORGE": automation_agent,
    "AUTOMATION": automation_agent,
    "SANDBOX": automation_agent,
    "OMNI": research_agent,
    "RESEARCH": research_agent,
    "KINESIS": document_agent,
    "DOCUMENT": document_agent,
    "CHRONOS": reminder_agent,
    "REMINDER": reminder_agent,
    "IRIS": vision_agent,
    "VISION": vision_agent,
    "PICASSO": image_agent,
    "IMAGE": image_agent,
    "CHAT": None,
    "SYNTHESIZER": None,
}


@dataclass
class TaskGraphResult:
    dag_id: str
    goal: str
    final_response: str
    tasks: list[SubTask]
    success: bool
    total_duration_ms: float
    execution_trace: list[dict[str, Any]] = field(default_factory=list)
    inter_agent_messages: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dag_id": self.dag_id,
            "goal": self.goal,
            "final_response": self.final_response,
            "tasks": [t.to_dict() for t in self.tasks],
            "success": self.success,
            "total_duration_ms": self.total_duration_ms,
            "execution_trace": self.execution_trace,
            "inter_agent_messages": self.inter_agent_messages,
            "artifacts": self.artifacts,
        }


class TaskGraphExecutor:
    """
    Asynchronous DAG Task Graph Orchestrator for Multi-Agent Collaboration.
    Dispatches tasks in parallel or sequence based on topological dependency resolution,
    shares state via the ContextBus, passes inter-agent messages, and synthesizes results.
    """

    def __init__(self):
        pass

    def _resolve_agent(self, agent_name: str):
        cleaned = agent_name.upper().strip()
        for k, v in AGENT_NAME_MAP.items():
            if k == cleaned or k in cleaned:
                return v
        return None

    def _substitute_placeholders(self, instruction: str, outputs: dict[str, Any]) -> str:
        """
        Replaces placeholders like {T1.output}, {T1}, {T2.1.output}, or {key}
        with corresponding output strings from previously executed tasks.
        """
        result = instruction
        for task_id, out in outputs.items():
            out_str = str(out) if out is not None else ""
            result = result.replace(f"{{{task_id}.output}}", out_str)
            result = result.replace(f"{{{task_id}}}", out_str)

        for key, out in outputs.items():
            out_str = str(out) if out is not None else ""
            result = result.replace(f"{{{key}}}", out_str)

        return result

    async def _execute_forge_sandbox_task(self, instruction: str) -> str:
        """
        Special execution for FORGE / Sandbox tasks:
        Extracts code if present and executes in Forge Sandbox or OS executor.
        """
        code_match = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", instruction)
        code_to_run = code_match.group(1) if code_match else instruction

        if "import " in code_to_run or "print(" in code_to_run or "def " in code_to_run:
            try:
                res = forge_sandbox.execute_python(code_to_run, timeout_seconds=15)
                output_str = f"Sandbox Execution Status: {res.get('status')}\nStdout:\n{res.get('stdout', '')}"
                if res.get("stderr"):
                    output_str += f"\nStderr:\n{res.get('stderr')}"
                if res.get("generated_files"):
                    output_str += f"\nGenerated Artifacts: {res.get('generated_files')}"
                return output_str
            except Exception as e:
                logger.warning(f"Forge Sandbox direct python execution fallback: {e}")

        # Fallback to normal automation agent
        return await automation_agent.run(instruction, history=[], memory_context="")

    async def execute_plan(
        self,
        plan: PlanResult,
        memory_context: str = "",
        session_id: str | None = None,
        on_event: Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]] | None = None,
    ) -> TaskGraphResult:
        """
        Executes a planned DAG of sub-tasks in dependency order:
        - Resolves unblocked nodes at each layer and runs them concurrently (`asyncio.gather`)
        - Shares context and publishes inter-agent messages through `context_bus`
        - Merges specialist outputs in the final synthesis stage
        """
        start_time = time.perf_counter()
        dag_id = f"dag_{uuid.uuid4().hex[:8]}"

        outputs_by_id: dict[str, Any] = {}
        outputs_by_key: dict[str, Any] = {}
        execution_trace: list[dict[str, Any]] = []
        artifacts: list[dict[str, Any]] = []

        # Store initial DAG meta in ContextBus
        await context_bus.set_context(dag_id, "goal", plan.goal)
        await context_bus.set_context(dag_id, "total_tasks", len(plan.tasks))

        start_payload = {
            "dag_id": dag_id,
            "goal": plan.goal,
            "total_tasks": len(plan.tasks),
            "tasks": [t.to_dict() for t in plan.tasks],
        }

        await context_bus.publish_event(session_id, dag_id, "task_graph_start", start_payload)
        if on_event:
            await on_event("task_graph_start", start_payload)

        completed_task_ids: set[str] = set()
        failed_task_ids: set[str] = set()

        while len(completed_task_ids) + len(failed_task_ids) < len(plan.tasks):
            # Find tasks whose dependencies have all completed
            ready_tasks: list[SubTask] = []
            for t in plan.tasks:
                if t.id not in completed_task_ids and t.id not in failed_task_ids and t.status == "pending":
                    deps_met = all(dep in completed_task_ids for dep in t.depends_on)
                    deps_failed = any(dep in failed_task_ids for dep in t.depends_on)

                    if deps_failed:
                        t.status = "failed"
                        t.error = f"Dependency failed in one of: {t.depends_on}"
                        failed_task_ids.add(t.id)
                    elif deps_met:
                        ready_tasks.append(t)

            if not ready_tasks:
                # Cycle detection or blocked state
                if len(completed_task_ids) + len(failed_task_ids) < len(plan.tasks):
                    for t in plan.tasks:
                        if t.id not in completed_task_ids and t.id not in failed_task_ids:
                            t.status = "failed"
                            t.error = "Unresolvable dependency or cycle detected in DAG"
                            failed_task_ids.add(t.id)
                break

            # Execute all ready tasks concurrently in this layer
            async def run_single_task(sub_task: SubTask):
                sub_task.status = "running"
                t_start = time.perf_counter()

                step_start_payload = {
                    "dag_id": dag_id,
                    "id": sub_task.id,
                    "agent": sub_task.agent,
                    "title": sub_task.title,
                    "instruction": sub_task.instruction,
                    "depends_on": sub_task.depends_on,
                }
                await context_bus.publish_event(session_id, dag_id, "task_graph_step_start", step_start_payload)
                if on_event:
                    await on_event("task_graph_step_start", step_start_payload)

                # Interpolate inputs from prior tasks
                merged_outputs = {**outputs_by_id, **outputs_by_key}
                interpolated_instruction = self._substitute_placeholders(
                    sub_task.instruction, merged_outputs
                )

                # Send handoff message from dependencies to this agent
                if sub_task.depends_on:
                    for dep_id in sub_task.depends_on:
                        dep_task = next((t for t in plan.tasks if t.id == dep_id), None)
                        dep_agent = dep_task.agent if dep_task else f"Task {dep_id}"
                        await context_bus.send_message(
                            dag_id=dag_id,
                            sender=dep_agent,
                            recipient=sub_task.agent,
                            message_type="data_transfer",
                            content=f"Transferred output from {dep_id} to {sub_task.agent} for task '{sub_task.title}'",
                            payload={"source_task": dep_id, "target_task": sub_task.id},
                            session_id=session_id,
                        )

                agent_inst = self._resolve_agent(sub_task.agent)
                try:
                    logger.info(f"NEXUS DAG [{dag_id}] executing sub-task {sub_task.id} with agent {sub_task.agent}")
                    
                    if sub_task.agent.upper() in ["FORGE", "SANDBOX"] and ("execute" in interpolated_instruction.lower() or "run" in interpolated_instruction.lower()):
                        res = await self._execute_forge_sandbox_task(interpolated_instruction)
                    elif agent_inst:
                        res = await agent_inst.run(
                            message=interpolated_instruction,
                            history=[],
                            memory_context=memory_context,
                        )
                    else:
                        from app.ai.llm.ollama_client import ollama_client
                        res = await ollama_client.chat(
                            messages=[{"role": "user", "content": interpolated_instruction}]
                        )

                    sub_task.output = res
                    sub_task.status = "done"
                    sub_task.execution_time_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
                    
                    outputs_by_id[sub_task.id] = res
                    if sub_task.output_key:
                        outputs_by_key[sub_task.output_key] = res
                        await context_bus.set_context(dag_id, sub_task.output_key, res)

                    await context_bus.set_context(dag_id, f"{sub_task.id}_output", res)
                    completed_task_ids.add(sub_task.id)

                    # Extract document artifact links if created
                    if "Document Artifact Created Successfully" in str(res):
                        url_match = re.search(r"Download URL\]:\s*\[(.*?)\]\((.*?)\)", str(res))
                        if url_match:
                            artifacts.append({
                                "name": url_match.group(1),
                                "url": url_match.group(2),
                                "agent": sub_task.agent,
                                "task_id": sub_task.id,
                            })

                    # Send status update message on bus
                    await context_bus.send_message(
                        dag_id=dag_id,
                        sender=sub_task.agent,
                        recipient="BUS",
                        message_type="status_update",
                        content=f"Task {sub_task.id} completed successfully in {sub_task.execution_time_ms}ms",
                        payload={"task_id": sub_task.id, "status": "done", "duration_ms": sub_task.execution_time_ms},
                        session_id=session_id,
                    )

                except Exception as e:
                    logger.error(f"Error executing sub-task {sub_task.id} ({sub_task.agent}): {e}")
                    sub_task.status = "failed"
                    sub_task.error = str(e)
                    sub_task.execution_time_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
                    failed_task_ids.add(sub_task.id)

                    await context_bus.send_message(
                        dag_id=dag_id,
                        sender=sub_task.agent,
                        recipient="BUS",
                        message_type="status_update",
                        content=f"Task {sub_task.id} failed: {e}",
                        payload={"task_id": sub_task.id, "status": "failed", "error": str(e)},
                        session_id=session_id,
                    )

                step_end_payload = {
                    "dag_id": dag_id,
                    "id": sub_task.id,
                    "agent": sub_task.agent,
                    "status": sub_task.status,
                    "output": str(sub_task.output)[:500] if sub_task.output else None,
                    "error": sub_task.error,
                    "execution_time_ms": sub_task.execution_time_ms,
                }
                await context_bus.publish_event(session_id, dag_id, "task_graph_step_end", step_end_payload)
                if on_event:
                    await on_event("task_graph_step_end", step_end_payload)

                execution_trace.append(sub_task.to_dict())

            await asyncio.gather(*(run_single_task(t) for t in ready_tasks))

        # Final Synthesis Step
        synthesis_spec = plan.synthesis or {"agent": "CHAT", "instruction": "Synthesize all specialist findings."}
        synth_inst_raw = synthesis_spec.get("instruction", "Synthesize the following outputs:")
        merged_outputs = {**outputs_by_id, **outputs_by_key}
        synth_instruction = self._substitute_placeholders(synth_inst_raw, merged_outputs)

        # Append detailed outputs block if placeholders were not comprehensive
        outputs_block = "\n\n".join(
            f"### Output from {t.agent} ({t.id} - {t.title}):\n{t.output or t.error}" for t in plan.tasks
        )
        synth_instruction = (
            f"{synth_instruction}\n\n"
            f"**Overall Objective:** {plan.goal}\n\n"
            f"**Specialist Agent Findings:**\n{outputs_block}\n\n"
            "Produce an authoritative, well-structured final synthesized response for the user with markdown formatting, code snippets, key insights, and artifact references."
        )

        synth_agent_name = synthesis_spec.get("agent", "CHAT")
        synth_agent = self._resolve_agent(synth_agent_name)

        await context_bus.send_message(
            dag_id=dag_id,
            sender="BUS",
            recipient=synth_agent_name,
            message_type="task_handoff",
            content=f"All sub-tasks completed. Dispatched to {synth_agent_name} for final synthesis.",
            session_id=session_id,
        )

        try:
            logger.info(f"NEXUS DAG [{dag_id}] executing final synthesis with {synth_agent_name}")
            if synth_agent:
                final_text = await synth_agent.run(
                    message=synth_instruction,
                    history=[],
                    memory_context=memory_context,
                )
            else:
                from app.ai.llm.ollama_client import ollama_client
                final_text = await ollama_client.chat(
                    messages=[{"role": "user", "content": synth_instruction}]
                )
        except Exception as e:
            logger.error(f"NEXUS synthesis error: {e}")
            final_text = f"NEXUS multi-agent collaboration completed:\n" + "\n".join(
                f"- **[{t.agent}] {t.title}:** {t.output or t.error}" for t in plan.tasks
            )

        elapsed_total = round((time.perf_counter() - start_time) * 1000.0, 2)
        success = len(failed_task_ids) == 0

        inter_agent_msgs = context_bus.get_messages(dag_id)

        result = TaskGraphResult(
            dag_id=dag_id,
            goal=plan.goal,
            final_response=final_text,
            tasks=plan.tasks,
            success=success,
            total_duration_ms=elapsed_total,
            execution_trace=execution_trace,
            inter_agent_messages=inter_agent_msgs,
            artifacts=artifacts,
        )

        # Record trace in ContextBus
        context_bus.record_trace(dag_id, result.to_dict())

        complete_payload = result.to_dict()
        await context_bus.publish_event(session_id, dag_id, "task_graph_complete", complete_payload)
        if on_event:
            await on_event("task_graph_complete", complete_payload)

        return result


task_graph_executor = TaskGraphExecutor()
