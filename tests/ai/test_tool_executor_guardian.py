import pytest
from app.ai.tools.executor import ToolExecutor, tool_executor
from app.ai.tools.registry import BaseTool, ToolRegistry


def test_parse_tool_call_xml():
    executor = ToolExecutor()
    llm_output = """I need to check the local files.
<tool_call>
{"tool": "file_read", "arguments": {"path": "main.py"}}
</tool_call>
Let me know if you need anything else."""

    call = executor.parse_tool_call(llm_output)
    assert call is not None
    assert call.tool == "file_read"
    assert call.arguments == {"path": "main.py"}


def test_parse_tool_call_markdown_json():
    registry = ToolRegistry()
    registry.register(BaseTool(name="web_search", description="search", parameters={"type": "object", "properties": {}}))
    executor = ToolExecutor(registry=registry)

    llm_output = """Here is the search tool call:
```json
{
  "tool": "web_search",
  "arguments": {
    "query": "local Ollama tool calling"
  }
}
```"""
    call = executor.parse_tool_call(llm_output)
    assert call is not None
    assert call.tool == "web_search"
    assert call.arguments["query"] == "local Ollama tool calling"


@pytest.mark.asyncio
async def test_guardian_safety_gate_blocking():
    # Attempting to execute destructive shell command through executor
    res = await tool_executor.execute(
        tool_name="shell_execute",
        arguments={"command": "rm -rf /"},
    )
    assert res.success is False
    assert "Blocked by Guardian" in res.error
    assert res.guardian_verdict is not None
    assert res.guardian_verdict["level"] == 3  # SAFETY level


@pytest.mark.asyncio
async def test_safe_tool_execution():
    res = await tool_executor.execute(
        tool_name="python_execute",
        arguments={"code": "print('Safe computation: 10 * 10 =', 10 * 10)"},
    )
    assert res.success is True
    assert res.error is None
    assert "Safe computation: 10 * 10 = 100" in res.output["stdout"]
    assert res.execution_time_ms >= 0.0

    xml_repr = res.format_xml()
    assert "<tool_result>" in xml_repr
    assert "Safe computation" in xml_repr
