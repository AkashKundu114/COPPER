import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.core.constants import AgentType
from app.core.logger import logger

NEXUS_PLANNER_PROMPT = """You are NEXUS, COPPER's internal Task Decomposition Planner.
You do NOT speak to the user. You are an internal orchestration process.
Given a complex user request, decompose it into a DAG of sub-tasks.

AVAILABLE AGENTS:
- CHAT (Llama-3.1-8B): Conversational, general knowledge
- AXIS (Qwen2.5-Coder-7B): Software engineering, code writing, debugging
- FORGE (Mistral-7B): OS automation, PowerShell, local filesystem operations
- KINESIS (Qwen2.5-7B): Document generation (PDF, DOCX, MD, HTML, CSV)
- CHRONOS (Llama-3.1-8B): Scheduling, reminders, calendar events
- OMNI (DeepSeek-R1-7B): Research, analysis, document RAG, web search
- IRIS (Qwen2-VL-7B): Visual analysis, screenshots, OCR
- PICASSO: Image generation

RULES:
1. Each sub-task must be atomic — one agent, one execution.
2. Specify dependencies explicitly (e.g. `depends_on: ["T1"]`). Independent tasks must have `depends_on: []` to run in parallel.
3. Maximum 6 sub-tasks. If more are needed, simplify the plan.
4. The final step is always SYNTHESIS — merging sub-task outputs into a coherent user-facing result.
5. If the request is simple and can be handled by a single agent, respond ONLY with:
<plan>SINGLE_AGENT: {agent_name}</plan>

RESPONSE FORMAT for decomposition:
<plan>
{
  "goal": "Brief description of the overall objective",
  "tasks": [
    {
      "id": "T1",
      "agent": "OMNI",
      "instruction": "Research...",
      "depends_on": [],
      "output_key": "research_findings"
    },
    {
      "id": "T2",
      "agent": "AXIS",
      "instruction": "Based on {T1.output}, implement...",
      "depends_on": ["T1"],
      "output_key": "code_solution"
    }
  ],
  "synthesis": {
    "agent": "CHAT",
    "instruction": "Synthesize {T1.output} and {T2.output} into a comprehensive response for the user."
  }
}
</plan>"""


@dataclass
class SubTask:
    id: str
    agent: str
    instruction: str
    depends_on: list[str] = field(default_factory=list)
    output_key: str = ""
    status: str = "pending"  # pending, running, done, failed
    output: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent": self.agent,
            "instruction": self.instruction,
            "depends_on": self.depends_on,
            "output_key": self.output_key,
            "status": self.status,
            "output": str(self.output)[:300] if self.output is not None else None,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class PlanResult:
    is_decomposition: bool
    target_agent: str | None = None
    goal: str = ""
    tasks: list[SubTask] = field(default_factory=list)
    synthesis: dict[str, Any] = field(default_factory=dict)
    raw_response: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_decomposition": self.is_decomposition,
            "target_agent": self.target_agent,
            "goal": self.goal,
            "tasks": [t.to_dict() for t in self.tasks],
            "synthesis": self.synthesis,
        }


class NexusPlanner:
    def __init__(self):
        self.model = model_manager.get_model("core_agents.reasoning", "deepseek-r1:7b")

    def should_consider_decomposition(self, message: str, router_confidence: float = 1.0) -> bool:
        """
        Fast heuristic to determine if a prompt is complex enough to invoke NEXUS:
        1. Length > 100 characters AND multiple action keywords (e.g. 'research and then code', 'search ... and create a pdf')
        2. OR router confidence is low (< 0.70)
        3. Explicit multi-step phrasing ('first ..., then ...', 'step 1, step 2', 'and also schedule')
        """
        msg_lower = message.lower()
        if len(message) < 50:
            return False

        multi_step_cues = [
            " and then ",
            " then create ",
            " then write ",
            " then generate ",
            " then save ",
            " then schedule ",
            " first ",
            " after that ",
            " also create a ",
            " also write a ",
            " and export to ",
            " research and code ",
            " search and document ",
            " analyze and build ",
        ]
        has_cue = any(cue in msg_lower for cue in multi_step_cues)

        action_verbs = ["search", "research", "find", "code", "implement", "write", "create", "generate", "document", "schedule", "remind", "test", "automate"]
        verb_count = sum(1 for v in action_verbs if f" {v} " in f" {msg_lower} ")

        if (len(message) > 80 and verb_count >= 2 and has_cue) or (len(message) > 120 and verb_count >= 3) or router_confidence < 0.60:
            return True

        return False

    async def plan(self, message: str, context: str = "") -> PlanResult:
        """
        Decomposes a request into a DAG of sub-tasks using the reasoning LLM.
        """
        messages = [
            {"role": "system", "content": NEXUS_PLANNER_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nUser Request: {message}"},
        ]

        try:
            raw = await ollama_client.chat(messages, model=self.model)
            return self._parse_plan_output(raw, fallback_message=message)
        except Exception as e:
            logger.error(f"NEXUS planning error: {e}")
            return PlanResult(is_decomposition=False, target_agent=AgentType.CHAT.value, raw_response=str(e))

    def _parse_plan_output(self, raw: str, fallback_message: str = "") -> PlanResult:
        match = re.search(r"<plan>(.*?)</plan>", raw, re.DOTALL | re.IGNORECASE)
        content = match.group(1).strip() if match else raw.strip()

        # Check for SINGLE_AGENT response
        if "SINGLE_AGENT:" in content.upper() or not content.startswith("{"):
            agent_match = re.search(r"SINGLE_AGENT:\s*([A-Za-z0-9_]+)", content, re.IGNORECASE)
            agent_name = agent_match.group(1).upper() if agent_match else "CHAT"
            return PlanResult(
                is_decomposition=False,
                target_agent=agent_name.lower(),
                raw_response=raw,
            )

        # Parse JSON DAG
        try:
            data = json.loads(content)
            goal = data.get("goal", "Multi-agent collaborative task")
            raw_tasks = data.get("tasks", [])
            synthesis = data.get("synthesis", {"agent": "CHAT", "instruction": "Synthesize all task outputs."})

            tasks = []
            for t in raw_tasks:
                tasks.append(
                    SubTask(
                        id=t.get("id", f"T{len(tasks)+1}"),
                        agent=t.get("agent", "CHAT").upper(),
                        instruction=t.get("instruction", ""),
                        depends_on=t.get("depends_on", []),
                        output_key=t.get("output_key", t.get("id", "output")),
                    )
                )

            if len(tasks) <= 1:
                # Only 1 sub-task, treat as single agent
                target = tasks[0].agent.lower() if tasks else "chat"
                return PlanResult(is_decomposition=False, target_agent=target, raw_response=raw)

            return PlanResult(
                is_decomposition=True,
                goal=goal,
                tasks=tasks,
                synthesis=synthesis,
                raw_response=raw,
            )

        except Exception as e:
            logger.warning(f"Failed to parse NEXUS JSON plan: {e}. Output was: {content[:200]}")
            return PlanResult(is_decomposition=False, target_agent="chat", raw_response=raw)


nexus_planner = NexusPlanner()
