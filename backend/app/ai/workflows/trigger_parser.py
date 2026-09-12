import json
import re
from dataclasses import dataclass, field
from typing import Any

from apscheduler.triggers.cron import CronTrigger

from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.ai.workflows.dsl import (
    ActionFailurePolicy,
    Condition,
    NotificationConfig,
    TriggerConfig,
    TriggerType,
    Workflow,
    WorkflowAction,
)
from app.core.logger import logger

DAEMON_SYSTEM_PROMPT = """You are DAEMON, COPPER's Workflow Automation Parser. Translate natural language into structured workflow definitions.

TRIGGER TYPES: cron (standard 5-field), interval, event (on_app_launch, on_file_change, on_idle), manual

AVAILABLE TOOLS: file_read, file_write, shell_execute, memory_query, web_search, calendar_create, python_execute

RESPONSE FORMAT:
{
  "name": "...",
  "description": "...",
  "trigger": {
    "type": "cron",
    "value": "0 9 * * MON-FRI"
  },
  "conditions": [],
  "actions": [
    {
      "tool": "...",
      "arguments": {},
      "on_failure": "skip"
    }
  ],
  "notification": {
    "type": "toast",
    "template": "..."
  },
  "enabled": true
}

If the user's intent or timing is ambiguous or requires unmappable tools, respond with:
{
  "clarification_needed": true,
  "questions": [
    "Clarification question 1...",
    "Clarification question 2..."
  ],
  "reason": "Explanation of ambiguity or missing tool capability"
}

RULES:
1. Be precise with cron. "Every morning" = "0 9 * * *". "Weekday mornings" = "0 9 * * MON-FRI".
2. If ambiguous timing, ask for clarification.
3. Map to existing tools. If unmappable, explain what's missing.
4. Output ONLY valid JSON, without any commentary or markdown wrapping."""

AVAILABLE_TOOLS = {
    "file_read",
    "file_write",
    "shell_execute",
    "memory_query",
    "web_search",
    "calendar_create",
    "python_execute",
}

VALID_TRIGGER_TYPES = {"cron", "interval", "event", "manual"}


@dataclass
class ParseResult:
    success: bool
    workflow: Workflow | None = None
    raw_json: dict[str, Any] | None = None
    questions: list[str] = field(default_factory=list)
    error: str | None = None


def validate_cron_expression(expr: str) -> tuple[bool, str | None]:
    """Validates 5-field cron expression using CronTrigger."""
    if not expr or not isinstance(expr, str):
        return False, "Cron expression must be a non-empty string"
    try:
        CronTrigger.from_crontab(expr.strip())
        return True, None
    except Exception as e:
        return False, f"Invalid cron expression '{expr}': {str(e)}"


def parse_interval_seconds(val: Any) -> tuple[bool, float | None, str | None]:
    """Parses interval values like '30s', '15m', '2h', or integer seconds into total seconds."""
    if isinstance(val, (int, float)):
        if val <= 0:
            return False, None, "Interval must be greater than 0 seconds"
        return True, float(val), None

    if not isinstance(val, str):
        return False, None, f"Unsupported interval format: {type(val)}"

    val_clean = val.strip().lower()
    match = re.match(r"^(\d+(?:\.\d+)?)\s*(s|sec|seconds?|m|min|minutes?|h|hr|hours?|d|days?)?$", val_clean)
    if not match:
        return False, None, f"Cannot parse interval string '{val}'"

    amount = float(match.group(1))
    unit = (match.group(2) or "s").lower()

    if unit.startswith("s"):
        secs = amount
    elif unit.startswith("m"):
        secs = amount * 60
    elif unit.startswith("h"):
        secs = amount * 3600
    elif unit.startswith("d"):
        secs = amount * 86400
    else:
        secs = amount

    if secs <= 0:
        return False, None, "Interval duration must be positive"
    return True, secs, None


def extract_json(text: str) -> dict[str, Any] | None:
    """Safely extracts a JSON object from text."""
    if not text:
        return None
    cleaned = text.strip()

    # If wrapped in markdown code blocks
    code_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", cleaned)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except Exception:
            pass

    # Find widest outermost braces
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except Exception:
            # Try removing trailing commas
            candidate = cleaned[start : end + 1]
            candidate = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(candidate)
            except Exception:
                pass

    return None


class TriggerParser:
    def __init__(self):
        self.available_tools = AVAILABLE_TOOLS

    def _heuristic_parse(self, prompt: str) -> ParseResult | None:
        """
        Fast deterministic heuristic parser for high-frequency patterns and zero-dependency fallbacks.
        Also detects obviously ambiguous requests (e.g. 'sometimes', 'when possible').
        """
        p_lower = prompt.strip().lower()

        # 1. Ambiguity detection
        ambiguous_triggers = [
            "sometime",
            "someday",
            "later",
            "when you can",
            "whenever",
            "randomly",
            "occasionally",
        ]
        if any(w in p_lower for w in ambiguous_triggers) and not any(
            t in p_lower for t in ["every", "at", "when i", "daily", "hourly"]
        ):
            return ParseResult(
                success=False,
                questions=[
                    "What specific time or frequency should this workflow run at (e.g. daily at 9:00 AM, or every hour)?",
                    "Should this trigger on a specific event like launching an app?",
                ],
                error="Ambiguous timing specified in prompt.",
            )

        # 2. Check for "Every morning at 9am, summarize my overdue tasks"
        if "every morning" in p_lower or "morning" in p_lower and "9am" in p_lower:
            cron_val = "0 9 * * *"
            if "weekday" in p_lower or "mon-fri" in p_lower or "workday" in p_lower:
                cron_val = "0 9 * * MON-FRI"

            actions = [
                WorkflowAction(
                    tool="memory_query",
                    arguments={"query": "overdue tasks and action items"},
                    on_failure=ActionFailurePolicy.SKIP,
                )
            ]
            return ParseResult(
                success=True,
                workflow=Workflow(
                    name="Morning Task Summary",
                    description="Summarize overdue tasks every morning at 9:00 AM",
                    trigger=TriggerConfig(type=TriggerType.CRON, value=cron_val),
                    conditions=[],
                    actions=actions,
                    notification=NotificationConfig(
                        type="toast",
                        template="Morning Briefing: Here is your overdue tasks summary:\n{result}",
                    ),
                    enabled=True,
                ),
            )

        # 3. Check for "When I open VS Code, load my project context"
        if "when i open" in p_lower or "on launch" in p_lower or "on open" in p_lower:
            app_target = "Code.exe"
            if "browser" in p_lower or "chrome" in p_lower:
                app_target = "chrome.exe"
            elif "terminal" in p_lower or "powershell" in p_lower:
                app_target = "powershell.exe"

            actions = [
                WorkflowAction(
                    tool="memory_query",
                    arguments={"query": "recent project context and active files"},
                    on_failure=ActionFailurePolicy.SKIP,
                )
            ]
            return ParseResult(
                success=True,
                workflow=Workflow(
                    name=f"Context Loader for {app_target}",
                    description=f"Load project context when {app_target} launches",
                    trigger=TriggerConfig(
                        type=TriggerType.EVENT,
                        value="on_app_launch",
                        metadata={"app": app_target},
                    ),
                    conditions=[],
                    actions=actions,
                    notification=NotificationConfig(
                        type="toast",
                        template="Project context loaded for " + app_target,
                    ),
                    enabled=True,
                ),
            )

        # 4. Check for "Every X minutes/hours/seconds"
        interval_match = re.search(r"every\s+(\d+)\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?|days?)", p_lower)
        if interval_match:
            qty = interval_match.group(1)
            unit = interval_match.group(2)
            unit_abbrev = "m" if "min" in unit else "h" if "h" in unit else "d" if "d" in unit else "s"
            val_str = f"{qty}{unit_abbrev}"

            # Infer tool action
            if "search" in p_lower or "web" in p_lower:
                tool = "web_search"
                args = {"query": prompt}
            elif "memory" in p_lower:
                tool = "memory_query"
                args = {"query": prompt}
            elif "python" in p_lower or "code" in p_lower:
                tool = "python_execute"
                args = {"code": "print('Automated workflow check')"}
            else:
                tool = "shell_execute"
                args = {"command": "echo Workflow check"}

            return ParseResult(
                success=True,
                workflow=Workflow(
                    name=f"Periodic Automation ({val_str})",
                    description=f"Automated workflow running every {qty} {unit}",
                    trigger=TriggerConfig(type=TriggerType.INTERVAL, value=val_str),
                    conditions=[],
                    actions=[WorkflowAction(tool=tool, arguments=args, on_failure=ActionFailurePolicy.SKIP)],
                    notification=NotificationConfig(type="toast", template="Workflow executed: {result}"),
                    enabled=True,
                ),
            )

        # 5. Check for "Every day at HH:MM" or "Daily at HH:MM"
        daily_match = re.search(r"(?:every day|daily)\s+at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", p_lower)
        if daily_match:
            hour = int(daily_match.group(1))
            minute = int(daily_match.group(2) or 0)
            meridiem = daily_match.group(3)
            if meridiem == "pm" and hour < 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
            cron_expr = f"{minute} {hour} * * *"

            return ParseResult(
                success=True,
                workflow=Workflow(
                    name=f"Daily Workflow at {hour:02d}:{minute:02d}",
                    description=f"Automated daily task scheduled at {hour:02d}:{minute:02d}",
                    trigger=TriggerConfig(type=TriggerType.CRON, value=cron_expr),
                    conditions=[],
                    actions=[
                        WorkflowAction(
                            tool="memory_query",
                            arguments={"query": prompt},
                            on_failure=ActionFailurePolicy.SKIP,
                        )
                    ],
                    notification=NotificationConfig(type="toast", template="Daily routine completed: {result}"),
                    enabled=True,
                ),
            )

        return None

    def validate_workflow_data(self, data: dict[str, Any]) -> ParseResult:
        """
        Validates parsed JSON against trigger constraints, available tools, and structure.
        """
        if data.get("clarification_needed"):
            questions = data.get("questions") or ["Could you provide more specific timing or details?"]
            reason = data.get("reason", "Clarification requested by DAEMON parser")
            return ParseResult(success=False, raw_json=data, questions=questions, error=reason)

        trigger_data = data.get("trigger", {})
        trigger_type = str(trigger_data.get("type", "")).strip().lower()
        trigger_val = trigger_data.get("value", "")

        if trigger_type not in VALID_TRIGGER_TYPES:
            return ParseResult(
                success=False,
                raw_json=data,
                questions=[
                    f"Unsupported trigger type '{trigger_type}'. Please specify 'cron', 'interval', 'event', or 'manual'."
                ],
                error=f"Invalid trigger type '{trigger_type}'",
            )

        # Validate cron expression
        if trigger_type == TriggerType.CRON.value:
            ok, err = validate_cron_expression(str(trigger_val))
            if not ok:
                return ParseResult(
                    success=False,
                    raw_json=data,
                    questions=[
                        f"The scheduled cron expression '{trigger_val}' was invalid: {err}.",
                        "What time of day or days of the week should this run (e.g. '0 9 * * *' for 9 AM daily)?",
                    ],
                    error=err,
                )

        # Validate interval
        if trigger_type == TriggerType.INTERVAL.value:
            ok, _, err = parse_interval_seconds(trigger_val)
            if not ok:
                return ParseResult(
                    success=False,
                    raw_json=data,
                    questions=[
                        f"The interval expression '{trigger_val}' was invalid: {err}.",
                        "How frequently should this run (e.g. '30s', '15m', or '2h')?",
                    ],
                    error=err,
                )

        # Validate actions and tool availability
        actions_raw = data.get("actions", [])
        if not actions_raw or not isinstance(actions_raw, list):
            return ParseResult(
                success=False,
                raw_json=data,
                questions=["What specific action or tool should be executed when triggered?"],
                error="Workflow must contain at least one action",
            )

        unmappable_tools = []
        parsed_actions: list[WorkflowAction] = []
        for i, a in enumerate(actions_raw):
            tool_name = str(a.get("tool", "")).strip()
            if tool_name not in self.available_tools:
                unmappable_tools.append(tool_name)
            else:
                parsed_actions.append(WorkflowAction.from_dict(a))

        if unmappable_tools:
            return ParseResult(
                success=False,
                raw_json=data,
                questions=[
                    f"Tool '{t}' is not an available COPPER workflow tool. Available tools are: {', '.join(sorted(self.available_tools))}."
                    for t in unmappable_tools
                ],
                error=f"Unmappable tools: {', '.join(unmappable_tools)}",
            )

        # Build Workflow object
        try:
            workflow = Workflow.from_dict(data)
            return ParseResult(success=True, workflow=workflow, raw_json=data)
        except Exception as e:
            return ParseResult(
                success=False,
                raw_json=data,
                questions=["Could not construct valid workflow from parsed definition."],
                error=f"Workflow instantiation error: {str(e)}",
            )

    async def parse(self, natural_language: str) -> ParseResult:
        """
        Translates a natural language user automation prompt into a structured Workflow definition.
        """
        clean_prompt = natural_language.strip()
        if not clean_prompt:
            return ParseResult(
                success=False,
                questions=["Please provide an instruction describing what automation you want to create."],
                error="Empty prompt",
            )

        # Check heuristic parser first for exact/obvious commands or quick resolution
        heuristic_res = self._heuristic_parse(clean_prompt)
        if heuristic_res is not None and not heuristic_res.success:
            # If heuristic detected clear ambiguity, return clarification
            return heuristic_res

        # Try LLM call if available
        llm_model = model_manager.get_model("subagents.router", "qwen2.5:1.5b")
        messages = [
            {"role": "system", "content": DAEMON_SYSTEM_PROMPT},
            {"role": "user", "content": clean_prompt},
        ]

        raw_response = ""
        try:
            if await ollama_client.is_available():
                raw_response = await ollama_client.chat(
                    messages=messages,
                    model=llm_model,
                    options={"temperature": 0.1},
                )
        except Exception as e:
            logger.debug(f"LLM call during trigger parsing failed: {e}")

        # If LLM returned a response, try to parse JSON
        if raw_response:
            parsed_json = extract_json(raw_response)
            if parsed_json:
                result = self.validate_workflow_data(parsed_json)
                return result

        # Fallback to heuristic parser if LLM failed or was offline
        if heuristic_res is not None:
            return heuristic_res

        # If neither heuristic nor LLM could produce a workflow, ask for clarification
        return ParseResult(
            success=False,
            questions=[
                "Could not automatically determine the trigger timing or tools for this request.",
                f"Please specify a schedule (e.g. 'every weekday at 9am') and tools from: {', '.join(sorted(self.available_tools))}.",
            ],
            error="Could not parse workflow from input",
        )


trigger_parser = TriggerParser()
