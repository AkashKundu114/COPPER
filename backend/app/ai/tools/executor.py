import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from app.ai.tools.builtin import *  # Ensure all builtins are imported & registered
from app.ai.tools.registry import BaseTool, tool_registry
from app.core.guardian import DisagreementLevel, GuardianVerdict, guardian_engine
from app.core.logger import logger


@dataclass
class ToolCall:
    tool: str
    arguments: dict[str, Any]
    raw: str = ""


@dataclass
class ToolResult:
    tool_name: str
    arguments: dict[str, Any]
    output: Any
    success: bool
    error: str | None = None
    guardian_verdict: dict[str, Any] | None = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool_name,
            "arguments": self.arguments,
            "output": self.output,
            "success": self.success,
            "error": self.error,
            "guardian_verdict": self.guardian_verdict,
            "execution_time_ms": self.execution_time_ms,
        }

    def format_xml(self) -> str:
        """Format as <tool_result>...</tool_result> XML tag for feeding back to LLM."""
        body = json.dumps(
            {
                "tool": self.tool_name,
                "status": "success" if self.success else "error",
                "result": self.output if self.success else self.error,
            },
            indent=2,
            default=str,
        )
        return f"<tool_result>\n{body}\n</tool_result>"


class ToolExecutor:
    def __init__(self, registry=tool_registry, max_steps: int = 5):
        self.registry = registry
        self.max_steps = max_steps

    def parse_tool_call(self, text: str) -> ToolCall | None:
        """
        Parses a tool call from LLM response text.
        Supports:
        1. Explicit XML tags: <tool_call>{"tool": "...", "arguments": {...}}</tool_call>
        2. Markdown fenced JSON containing "tool" and "arguments"
        3. Raw JSON object with "tool" (or "name") and "arguments" (or "parameters")
        """
        if not text:
            return None

        # Pattern 1: <tool_call>...</tool_call>
        xml_match = re.search(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL | re.IGNORECASE)
        if xml_match:
            raw_json = xml_match.group(1).strip()
            parsed = self._safe_parse_json(raw_json)
            if parsed:
                tool_name = parsed.get("tool") or parsed.get("name")
                args = parsed.get("arguments") or parsed.get("parameters") or {}
                if tool_name:
                    return ToolCall(tool=str(tool_name).strip(), arguments=args, raw=xml_match.group(0))

        # Pattern 2: Markdown JSON code block with "tool" / "arguments"
        code_blocks = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
        for block in code_blocks:
            parsed = self._safe_parse_json(block)
            if parsed and ("tool" in parsed or "name" in parsed):
                tool_name = parsed.get("tool") or parsed.get("name")
                args = parsed.get("arguments") or parsed.get("parameters") or {}
                if tool_name and self.registry.get(str(tool_name).strip()):
                    return ToolCall(tool=str(tool_name).strip(), arguments=args, raw=block)

        # Pattern 3: Clean top-level JSON object
        trimmed = text.strip()
        if (trimmed.startswith("{") and trimmed.endswith("}")) or ("\"tool\":" in trimmed and "\"arguments\":" in trimmed):
            json_candidate = re.search(r"\{[\s\S]*\}", trimmed)
            if json_candidate:
                parsed = self._safe_parse_json(json_candidate.group(0))
                if parsed and ("tool" in parsed or "name" in parsed):
                    tool_name = parsed.get("tool") or parsed.get("name")
                    args = parsed.get("arguments") or parsed.get("parameters") or {}
                    if tool_name and self.registry.get(str(tool_name).strip()):
                        return ToolCall(tool=str(tool_name).strip(), arguments=args, raw=json_candidate.group(0))

        return None

    def _safe_parse_json(self, raw: str) -> dict | None:
        try:
            return json.loads(raw)
        except Exception:
            # Try cleaning trailing commas or relaxed parsing
            cleaned = re.sub(r",\s*([\]}])", r"\1", raw)
            try:
                return json.loads(cleaned)
            except Exception:
                return None

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: dict[str, Any] | None = None,
        on_event: Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]] | None = None,
    ) -> ToolResult:
        """
        Execute a single tool call with parameter validation, Guardian safety gating,
        and execution timing.
        """
        start_time = time.perf_counter()
        if context is None:
            context = {}

        tool = self.registry.get(tool_name)
        if not tool:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            err_msg = f"Unknown tool '{tool_name}'. Available tools: {', '.join(t.name for t in self.registry.list_tools())}"
            logger.warning(err_msg)
            return ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                output=None,
                success=False,
                error=err_msg,
                execution_time_ms=round(elapsed_ms, 2),
            )

        # 1. Validate Arguments
        valid, validation_err = tool.validate_args(arguments)
        if not valid:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                output=None,
                success=False,
                error=f"Argument validation failed: {validation_err}",
                execution_time_ms=round(elapsed_ms, 2),
            )

        # 2. Guardian Safety Check
        # Build action summary string
        action_summary = f"{tool_name}({', '.join(f'{k}={repr(v)[:50]}' for k, v in arguments.items())})"
        guardian_context = {
            **context,
            "tool_name": tool_name,
            "guardian_level": tool.guardian_level,
            "is_destructive": tool.guardian_level >= 3 or arguments.get("mode") == "overwrite",
        }

        # Check safety triggers in arguments (e.g. command or path)
        if "command" in arguments:
            action_summary += f" command: {arguments['command']}"

        verdict: GuardianVerdict = guardian_engine.evaluate(action_summary, guardian_context)

        if verdict.level == DisagreementLevel.SAFETY or (verdict.requires_confirmation and tool.guardian_level >= 3):
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            block_msg = f"Blocked by Guardian Safety Gate (Level {verdict.level.name}): {verdict.reasoning} Recommendation: {verdict.recommendation}"
            logger.warning(f"Guardian blocked tool '{tool_name}': {block_msg}")
            return ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                output=None,
                success=False,
                error=block_msg,
                guardian_verdict=verdict.to_dict(),
                execution_time_ms=round(elapsed_ms, 2),
            )

        # Emit start event if hook provided
        if on_event:
            try:
                await on_event(
                    "tool_call_start",
                    {
                        "tool": tool_name,
                        "arguments": arguments,
                        "guardian_verdict": verdict.to_dict(),
                    },
                )
            except Exception as ev_err:
                logger.debug(f"Tool event callback error: {ev_err}")

        # 3. Execute Tool
        try:
            output = await tool.execute(**arguments)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            result = ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                output=output,
                success=isinstance(output, dict) is False or output.get("status") != "error",
                error=output.get("error") if isinstance(output, dict) and output.get("status") == "error" else None,
                guardian_verdict=verdict.to_dict(),
                execution_time_ms=round(elapsed_ms, 2),
            )

            # Emit end event
            if on_event:
                try:
                    await on_event(
                        "tool_call_end",
                        {
                            "tool": tool_name,
                            "success": result.success,
                            "output": output,
                            "execution_time_ms": result.execution_time_ms,
                        },
                    )
                except Exception as ev_err:
                    logger.debug(f"Tool event callback error: {ev_err}")

            return result

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Tool execution exception for '{tool_name}': {e}")
            return ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                output=None,
                success=False,
                error=f"Execution error: {str(e)}",
                guardian_verdict=verdict.to_dict(),
                execution_time_ms=round(elapsed_ms, 2),
            )


tool_executor = ToolExecutor()
