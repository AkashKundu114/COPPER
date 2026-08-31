import asyncio
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from app.ai.agents.automation_agent import automation_agent
from app.ai.agents.coding_agent import coding_agent
from app.ai.agents.document_agent import document_agent
from app.ai.agents.image_agent import image_agent
from app.ai.agents.reminder_agent import reminder_agent
from app.ai.agents.research_agent import research_agent
from app.ai.agents.vision_agent import vision_agent
from app.ai.orchestration.planner import PlanResult, SubTask
from app.core.constants import AgentType
from app.core.logger import logger

AGENT_NAME_MAP = {
    "AXIS": coding_agent,
    "CODING": coding_agent,
    "FORGE": automation_agent,
    "AUTOMATION": automation_agent,
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
    "CHAT": None,  # Will fallback to standard chat/LLM invocation
}


@dataclass
class TaskGraphResult:
    goal: str
    final_response: str
    tasks: list[SubTask]
    success: bool
    total_duration_ms: float
    execution_trace: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "final_response": self.final_response,
            "tasks": [t.to_dict() for t in self.tasks],
            "success": self.success,
            "total_duration_ms": self.total_duration_ms,
            "execution_trace": self.execution_trace,
        }


class TaskGraphExecutor:
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
        Replaces placeholders like {T1.output}, {T1.output_key}, {T1}, or {key}
        with corresponding output strings from previously executed tasks.
        """
        result = instruction
        for task_id, out in outputs.items():
            out_str = str(out) if out is not None else ""
            result = result.replace(f"{{{task_id}.output}}", out_str)
            result = result.replace(f"{{{task_id}}}", out_str)

        # Also substitute by output_key
        for key, out in outputs.items():
            out_str = str(out) if out is not None else ""
            result = result.replace(f"{{{key}}}", out_str)

        return result

    async def execute_plan(
        self,
        plan: PlanResult,
        memory_context: str = "",
        on_event: Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]] | None = None,
    ) -> TaskGraphResult:
        """
        Executes a planned DAG of sub-tasks in dependency order, running independent
        tasks in parallel, and finally executing the synthesis task.
        """
        start_time = time.perf_counter()
        task_map: dict[str, SubTask] = {t.id: t for t in plan.tasks}
        outputs_by_id: dict[str, Any] = {}
        outputs_by_key: dict[str, Any] = {}
        execution_trace: list[dict[str, Any]] = []

        if on_event:
            await on_event(
                "task_graph_start",
                {
                    "goal": plan.goal,
                    "total_tasks": len(plan.tasks),
                    "tasks": [t.to_dict() for t in plan.tasks],
                },
            )

        completed_task_ids: set[str] = set()
        failed_task_ids: set[str] = set()

        while len(completed_task_ids) + len(failed_task_ids) < len(plan.tasks):
            # Find tasks whose dependencies have all completed
            ready_tasks: list[SubTask] = []
            for t in plan.tasks:
                if t.id not in completed_task_ids and t.id not in failed_task_ids and t.status == "pending":
                    # Check if all dependencies are in completed_task_ids
                    deps_met = all(dep in completed_task_ids for dep in t.depends_on)
                    deps_failed = any(dep in failed_task_ids for dep in t.depends_on)

                    if deps_failed:
                        t.status = "failed"
                        t.error = f"Dependency failed in one of: {t.depends_on}"
                        failed_task_ids.add(t.id)
                    elif deps_met:
                        ready_tasks.append(t)

            if not ready_tasks:
                if len(completed_task_ids) + len(failed_task_ids) < len(plan.tasks):
                    # Circular dependency or unresolvable tasks
                    for t in plan.tasks:
                        if t.id not in completed_task_ids and t.id not in failed_task_ids:
                            t.status = "failed"
                            t.error = "Unresolvable dependency or cycle detected in DAG"
                            failed_task_ids.add(t.id)
                break

            # Execute ready tasks in parallel
            async def run_single_task(sub_task: SubTask):
                sub_task.status = "running"
                t_start = time.perf_counter()

                if on_event:
                    await on_event("task_graph_step_start", sub_task.to_dict())

                # Substitute outputs in instruction
                merged_outputs = {**outputs_by_id, **outputs_by_key}
                interpolated_instruction = self._substitute_placeholders(
                    sub_task.instruction, merged_outputs
                )

                agent_inst = self._resolve_agent(sub_task.agent)
                try:
                    logger.info(f"NEXUS executing sub-task {sub_task.id} with agent {sub_task.agent}")
                    if agent_inst:
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
                    completed_task_ids.add(sub_task.id)

                except Exception as e:
                    logger.error(f"Error executing sub-task {sub_task.id} ({sub_task.agent}): {e}")
                    sub_task.status = "failed"
                    sub_task.error = str(e)
                    sub_task.execution_time_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
                    failed_task_ids.add(sub_task.id)

                if on_event:
                    await on_event("task_graph_step_end", sub_task.to_dict())

                execution_trace.append(sub_task.to_dict())

            await asyncio.gather(*(run_single_task(t) for t in ready_tasks))

        # Final Synthesis Step
        synthesis_spec = plan.synthesis or {"agent": "CHAT", "instruction": "Synthesize results."}
        synth_inst_raw = synthesis_spec.get("instruction", "Synthesize the following outputs:")
        merged_outputs = {**outputs_by_id, **outputs_by_key}
        synth_instruction = self._substitute_placeholders(synth_inst_raw, merged_outputs)

        # If placeholders weren't explicitly used, append all task outputs
        if not any(f"{{{k}" in synth_inst_raw for k in outputs_by_id):
            outputs_block = "\n\n".join(
                f"### Output from {t.agent} ({t.id}):\n{t.output or t.error}" for t in plan.tasks
            )
            synth_instruction = f"{synth_instruction}\n\nTask Goal: {plan.goal}\n\nSub-Task Results:\n{outputs_block}"

        synth_agent_name = synthesis_spec.get("agent", "CHAT")
        synth_agent = self._resolve_agent(synth_agent_name)

        try:
            logger.info(f"NEXUS executing final synthesis with {synth_agent_name}")
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
            final_text = f"NEXUS multi-agent collaboration completed with errors:\n" + "\n".join(
                f"- [{t.agent}]: {t.output or t.error}" for t in plan.tasks
            )

        elapsed_total = round((time.perf_counter() - start_time) * 1000.0, 2)
        success = len(failed_task_ids) == 0

        result = TaskGraphResult(
            goal=plan.goal,
            final_response=final_text,
            tasks=plan.tasks,
            success=success,
            total_duration_ms=elapsed_total,
            execution_trace=execution_trace,
        )

        if on_event:
            await on_event("task_graph_complete", result.to_dict())

        return result


task_graph_executor = TaskGraphExecutor()
