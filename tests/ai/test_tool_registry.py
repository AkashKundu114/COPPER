import pytest
from app.ai.tools.registry import BaseTool, ToolRegistry


def test_tool_registry_registration():
    registry = ToolRegistry()

    @registry.tool(
        name="dummy_tool",
        description="A test tool",
        parameters={
            "type": "object",
            "properties": {"arg1": {"type": "string", "description": "test arg"}},
            "required": ["arg1"],
        },
        return_description="Test output",
        guardian_level=1,
    )
    def dummy_func(arg1: str):
        return f"Echo: {arg1}"

    tool = registry.get("dummy_tool")
    assert tool is not None
    assert tool.name == "dummy_tool"
    assert tool.guardian_level == 1
    assert tool.return_description == "Test output"


def test_tool_argument_validation():
    registry = ToolRegistry()

    tool = BaseTool(
        name="test_tool",
        description="Validation test",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "string param"},
                "count": {"type": "integer", "description": "int param"},
            },
            "required": ["text"],
        },
        return_description="val",
    )

    # Valid args
    valid, err = tool.validate_args({"text": "hello", "count": 5})
    assert valid is True
    assert err is None

    # Missing required arg
    valid, err = tool.validate_args({"count": 5})
    assert valid is False
    assert "Missing required" in err

    # Type mismatch: string expected, int provided
    valid, err = tool.validate_args({"text": 123})
    assert valid is False
    assert "must be a string" in err

    # Type mismatch: integer expected, boolean provided
    valid, err = tool.validate_args({"text": "ok", "count": True})
    assert valid is False
    assert "must be an integer" in err


def test_tool_schema_rendering():
    registry = ToolRegistry()

    @registry.tool(
        name="alpha_tool",
        description="First tool",
        parameters={
            "type": "object",
            "properties": {"q": {"type": "string", "description": "query string"}},
            "required": ["q"],
        },
        guardian_level=2,
    )
    def alpha_fn(q: str):
        return q

    rendered = registry.render_tool_schemas(["alpha_tool"])
    assert "**alpha_tool**" in rendered
    assert "[GUARDIAN_GATED: Level 2]" in rendered
    assert "- q [string] (required)" in rendered


def test_agent_tool_bindings():
    registry = ToolRegistry()

    registry.register(
        BaseTool(
            name="tool_a",
            description="A",
            parameters={"type": "object", "properties": {}},
        )
    )
    registry.register(
        BaseTool(
            name="tool_b",
            description="B",
            parameters={"type": "object", "properties": {}},
        )
    )

    registry.register_agent_tools("coding", ["tool_a"])
    registry.register_agent_tools("research", ["tool_a", "tool_b"])

    coding_tools = registry.get_tools_for_agent("coding")
    assert len(coding_tools) == 1
    assert coding_tools[0].name == "tool_a"

    research_tools = registry.get_tools_for_agent("research")
    assert len(research_tools) == 2
