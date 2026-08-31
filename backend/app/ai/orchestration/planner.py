import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.core.constants import AgentType
from app.core.logger import logger

NEXUS_PLANNER_PROMPT = """You are NEXUS, COPPER's Autonomous Multi-Agent Collaboration and Task Decomposition Planner.
You do NOT speak directly to the user. You are an internal cognitive planning engine powered by DeepSeek-R1 reasoning.
Given a complex user request, you decompose it into a Directed Acyclic Graph (DAG) of atomic sub-tasks delegated to specialist agents.

SPECIALIST AGENT SQUAD:
- OMNI (Research & Analysis): Data analysis, CSV/document inspection, mathematical insights, web research, fact extraction
- AXIS (Coding Engineer): Software architecture, writing Python/JS/Rust code, visualization scripts (matplotlib/seaborn), debugging
- FORGE (Sandbox & OS Automation): Sandboxed execution of scripts, capturing generated chart images, filesystem operations, shell execution
- KINESIS (Document Architect): Composing and generating professional PDF, DOCX, Markdown, HTML, CSV reports and presentation artifacts
- CHRONOS (Temporal & Reminders): Scheduling reminders, calendar events, agenda management
- IRIS (Vision & OCR): Image inspection, OCR, diagram understanding
- PICASSO (Image Studio): Image creation and visual asset generation
- CHAT (Master Synthesizer): Conversational interface, merging specialist findings into an authoritative final response

DECOMPOSITION RULES:
1. Atomic Tasks: Each task must have a single assigned specialist agent.
2. Dependencies: Specify dependencies explicitly (e.g. `depends_on: ["T1"]` or `depends_on: ["T1", "T2.1"]`). Independent tasks must have `depends_on: []` to run in parallel.
3. Nested & Sequential Workflows: For code execution pipelines, pair AXIS (code generation) with FORGE (execution in sandbox), e.g. T2 (AXIS writes script) -> T2.1 (FORGE executes script in sandbox and outputs chart image).
4. Inter-Task Context: Use placeholders like `{T1.output}`, `{T2.1.output}`, or `{output_key}` in downstream instructions so outputs flow cleanly.
5. Max 6 Sub-Tasks: Keep DAGs concise, high-impact, and non-redundant.
6. Single-Agent Bypass: If the user request is simple and requires only ONE specialist (e.g., just asking a coding question or just a reminder), respond ONLY with:
<plan>SINGLE_AGENT: {agent_name}</plan>

EXAMPLE COLLABORATIVE FLOW:
User: "Analyze this CSV sales data, write a Python script to visualize trends, and create a PDF report with the findings"
Output:
<plan>
{
  "goal": "Analyze sales data, visualize trends via Python, and generate a comprehensive PDF executive report",
  "tasks": [
    {
      "id": "T1",
      "agent": "OMNI",
      "title": "Analyze CSV Data & Extract Key Insights",
      "instruction": "Analyze the sales CSV data, identify revenue growth trends, top-performing product categories, and calculate quarterly growth metrics.",
      "depends_on": [],
      "output_key": "sales_insights"
    },
    {
      "id": "T2",
      "agent": "AXIS",
      "title": "Author Matplotlib Visualization Script",
      "instruction": "Write a clean Python script using matplotlib/seaborn to plot sales growth curves and categorical revenue breakdown based on {T1.output}.",
      "depends_on": ["T1"],
      "output_key": "plot_script"
    },
    {
      "id": "T2.1",
      "agent": "FORGE",
      "title": "Execute Plot Script in Sandbox & Capture Chart",
      "instruction": "Execute the Python visualization script {T2.output} inside the Forge sandbox environment and capture the generated chart output image.",
      "depends_on": ["T2"],
      "output_key": "chart_artifact"
    },
    {
      "id": "T3",
      "agent": "KINESIS",
      "title": "Generate Final PDF Executive Report",
      "instruction": "Generate a downloadable PDF executive report combining the sales insights from {T1.output} and referencing the generated visualization charts from {T2.1.output}.",
      "depends_on": ["T1", "T2.1"],
      "output_key": "pdf_report"
    }
  ],
  "synthesis": {
    "agent": "CHAT",
    "instruction": "Synthesize the sales insights {T1.output}, visualization code {T2.output}, and PDF report artifact {T3.output} into a polished, executive-ready summary."
  }
}
</plan>

Respond strictly in `<plan>...</plan>` tags."""


@dataclass
class SubTask:
    id: str
    agent: str
    instruction: str
    title: str = ""
    depends_on: list[str] = field(default_factory=list)
    output_key: str = ""
    status: str = "pending"  # pending, running, done, failed
    output: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0

    def __post_init__(self):
        if not self.title:
            self.title = f"Task {self.id} ({self.agent})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent": self.agent,
            "title": self.title,
            "instruction": self.instruction,
            "depends_on": self.depends_on,
            "output_key": self.output_key,
            "status": self.status,
            "output": str(self.output)[:500] if self.output is not None else None,
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
    thinking: str = ""
    raw_response: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_decomposition": self.is_decomposition,
            "target_agent": self.target_agent,
            "goal": self.goal,
            "tasks": [t.to_dict() for t in self.tasks],
            "synthesis": self.synthesis,
            "thinking": self.thinking[:300] if self.thinking else "",
        }


class NexusPlanner:
    def __init__(self):
        self.model = model_manager.get_model("core_agents.reasoning", "deepseek-r1:7b")

    def should_consider_decomposition(self, message: str, router_confidence: float = 1.0) -> bool:
        """
        Fast heuristic to determine if a prompt warrants NEXUS multi-agent decomposition:
        1. Explicit multi-action requests (e.g. analyze + code + PDF, research + implement + test)
        2. Multi-step keywords ('first..., then...', 'and also create a PDF', 'write a script and execute')
        3. Low router confidence or complex queries (>80 chars with multiple action verbs)
        """
        msg_lower = message.lower()
        if len(message) < 40:
            return False

        multi_step_cues = [
            " and then ",
            " then create ",
            " then write ",
            " then generate ",
            " then save ",
            " then schedule ",
            " then execute ",
            " then run ",
            " first ",
            " after that ",
            " also create a ",
            " also write a ",
            " and export to ",
            " and generate a pdf ",
            " and create a pdf ",
            " and write a python ",
            " and write a script ",
            " research and code ",
            " search and document ",
            " analyze and build ",
            " analyze and visualize ",
            " analyze this csv ",
            " visualize trends and create ",
            " multi-agent ",
            " workflow ",
            " pipeline ",
            " decompose ",
        ]
        has_cue = any(cue in msg_lower for cue in multi_step_cues)

        action_verbs = [
            "search", "research", "find", "code", "implement", "write",
            "create", "generate", "document", "schedule", "remind", "test",
            "automate", "analyze", "visualize", "execute", "export", "plot"
        ]
        verb_count = sum(1 for v in action_verbs if f" {v} " in f" {msg_lower} ")

        if has_cue and verb_count >= 2:
            return True
        if (len(message) > 80 and verb_count >= 3) or router_confidence < 0.60:
            return True

        return False

    async def plan(self, message: str, context: str = "") -> PlanResult:
        """
        Decomposes a request into a DAG of sub-tasks using the DeepSeek-R1 reasoning model.
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
        # Extract DeepSeek-R1 <think> block if present
        thinking_text = ""
        think_match = re.search(r"<think>(.*?)</think>", raw, re.DOTALL | re.IGNORECASE)
        if think_match:
            thinking_text = think_match.group(1).strip()

        # Extract <plan> block
        match = re.search(r"<plan>(.*?)</plan>", raw, re.DOTALL | re.IGNORECASE)
        content = match.group(1).strip() if match else raw.strip()

        # Strip think tags from content if still remaining
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE).strip()

        # Check for SINGLE_AGENT response
        if "SINGLE_AGENT:" in content.upper() or (not content.startswith("{") and "{" not in content):
            agent_match = re.search(r"SINGLE_AGENT:\s*([A-Za-z0-9_]+)", content, re.IGNORECASE)
            agent_name = agent_match.group(1).upper() if agent_match else "CHAT"
            return PlanResult(
                is_decomposition=False,
                target_agent=agent_name.lower(),
                thinking=thinking_text,
                raw_response=raw,
            )

        # Extract JSON substring if wrapped in markdown or extra text
        json_content = content
        if "{" in content and "}" in content:
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            json_content = content[start_idx:end_idx]

        # Parse JSON DAG
        try:
            data = json.loads(json_content)
            goal = data.get("goal", "Multi-agent collaborative task")
            raw_tasks = data.get("tasks", [])
            synthesis = data.get("synthesis", {"agent": "CHAT", "instruction": "Synthesize all task outputs."})

            tasks = []
            for t in raw_tasks:
                task_id = str(t.get("id", f"T{len(tasks)+1}"))
                tasks.append(
                    SubTask(
                        id=task_id,
                        agent=str(t.get("agent", "CHAT")).upper(),
                        title=str(t.get("title", f"Task {task_id}")),
                        instruction=str(t.get("instruction", "")),
                        depends_on=[str(d) for d in t.get("depends_on", [])],
                        output_key=str(t.get("output_key", task_id)),
                    )
                )

            if len(tasks) <= 1:
                # Only 1 sub-task, treat as single agent
                target = tasks[0].agent.lower() if tasks else "chat"
                return PlanResult(
                    is_decomposition=False,
                    target_agent=target,
                    thinking=thinking_text,
                    raw_response=raw,
                )

            return PlanResult(
                is_decomposition=True,
                goal=goal,
                tasks=tasks,
                synthesis=synthesis,
                thinking=thinking_text,
                raw_response=raw,
            )

        except Exception as e:
            logger.warning(f"Failed to parse NEXUS JSON plan: {e}. Output was: {content[:200]}")
            return PlanResult(
                is_decomposition=False,
                target_agent="chat",
                thinking=thinking_text,
                raw_response=raw,
            )


nexus_planner = NexusPlanner()
