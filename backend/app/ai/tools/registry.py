import inspect
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from app.core.logger import logger


@dataclass
class BaseTool:
    name: str
    description: str
    parameters: dict[str, Any]
    return_description: str = "Result of tool execution"
    guardian_level: int = 0  # 0: EXECUTE, 1: SUGGEST, 2: CHALLENGE, 3: SAFETY
    func: Callable[..., Any | Coroutine[Any, Any, Any]] | None = None

    def validate_args(self, args: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate provided arguments against the tool's JSON schema."""
        if not isinstance(args, dict):
            return False, f"Arguments must be a JSON dictionary, got {type(args).__name__}"

        schema_props = self.parameters.get("properties", {})
        required = self.parameters.get("required", [])

        # Check for missing required fields
        missing = [req for req in required if req not in args]
        if missing:
            return False, f"Missing required arguments: {', '.join(missing)}"

        # Type checks for basic primitive types
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        for param_name, val in args.items():
            if param_name in schema_props:
                expected_type_str = schema_props[param_name].get("type")
                if expected_type_str in type_map:
                    expected_type = type_map[expected_type_str]
                    # Note: bool is a subclass of int in Python, so special check for boolean vs integer
                    if expected_type_str == "integer" and isinstance(val, bool):
                        return False, f"Argument '{param_name}' must be an integer, got boolean"
                    if not isinstance(val, expected_type):
                        return False, f"Argument '{param_name}' must be a {expected_type_str}, got {type(val).__name__}"

        return True, None

    async def execute(self, **kwargs) -> Any:
        """Execute the underlying function with kwargs."""
        if self.func is None:
            raise NotImplementedError(f"Tool {self.name} has no implementation function.")

        if inspect.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        return self.func(**kwargs)

    def to_schema(self) -> dict[str, Any]:
        """Return standardized OpenAI/Ollama function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._agent_bindings: dict[str, list[str]] = {}

    def register(self, tool: BaseTool) -> BaseTool:
        """Register a tool in the global registry."""
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool '{tool.name}' (Guardian Level {tool.guardian_level})")
        return tool

    def tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        return_description: str = "Result of tool execution",
        guardian_level: int = 0,
    ):
        """Decorator for registering a tool function directly."""

        def decorator(fn: Callable[..., Any]):
            tool_obj = BaseTool(
                name=name,
                description=description,
                parameters=parameters,
                return_description=return_description,
                guardian_level=guardian_level,
                func=fn,
            )
            self.register(tool_obj)
            return fn

        return decorator

    def get(self, name: str) -> BaseTool | None:
        """Retrieve tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_schemas(self, tool_names: list[str] | None = None) -> list[dict[str, Any]]:
        """Get list of function schemas for given tool names (or all tools)."""
        if tool_names is None:
            tools = self._tools.values()
        else:
            tools = [self._tools[t] for t in tool_names if t in self._tools]
        return [t.to_schema() for t in tools]

    def render_tool_schemas(self, tool_names: list[str] | None = None) -> str:
        """
        Renders tool definitions into a clean text block for inclusion in the system prompt.
        """
        if tool_names is None:
            tools = list(self._tools.values())
        else:
            tools = [self._tools[t] for t in tool_names if t in self._tools]

        if not tools:
            return "No tools available."

        rendered = []
        for t in tools:
            guard_tag = f" [GUARDIAN_GATED: Level {t.guardian_level}]" if t.guardian_level > 0 else ""
            props = t.parameters.get("properties", {})
            required = t.parameters.get("required", [])

            args_desc = []
            for prop_name, prop_info in props.items():
                req_marker = " (required)" if prop_name in required else " (optional)"
                prop_type = prop_info.get("type", "any")
                prop_desc = prop_info.get("description", "")
                args_desc.append(f"    - {prop_name} [{prop_type}]{req_marker}: {prop_desc}")

            args_block = "\n".join(args_desc) if args_desc else "    (No arguments required)"

            rendered.append(
                f"- **{t.name}**{guard_tag}: {t.description}\n"
                f"  Parameters:\n{args_block}\n"
                f"  Returns: {t.return_description}"
            )

        return "\n\n".join(rendered)

    def register_agent_tools(self, agent_type: str, tool_names: list[str]):
        """Bind default tool names to a specific agent type."""
        self._agent_bindings[str(agent_type).lower()] = tool_names

    def get_tools_for_agent(self, agent_type: str) -> list[BaseTool]:
        """Get all BaseTool instances bound to an agent type."""
        names = self._agent_bindings.get(str(agent_type).lower(), [])
        return [self._tools[n] for n in names if n in self._tools]


tool_registry = ToolRegistry()
