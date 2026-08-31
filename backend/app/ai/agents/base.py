from collections.abc import AsyncGenerator

from app.ai.llm.ollama_client import ollama_client
from app.ai.tools.executor import tool_executor
from app.ai.tools.registry import tool_registry
from app.core.constants import AgentType, LLMProvider
from app.core.logger import logger

SYSTEM_TOOL_TEMPLATE = """You are {name} within C.O.P.P.E.R.
{description}

AVAILABLE TOOLS:
{rendered_tool_schemas}

HOW TO USE TOOLS:
When you need to perform an action or retrieve information, emit a JSON tool call inside <tool_call> tags:
<tool_call>
{{"tool": "tool_name", "arguments": {{"param1": "value1"}}}}
</tool_call>

You will receive the result inside <tool_result> tags before you continue.

RULES:
1. Think before acting. Explain your reasoning, then emit the tool call.
2. You may chain multiple tool calls across steps. Each observation feeds your next decision.
3. NEVER fabricate or hallucinate tool results.
4. Maximum {max_tool_steps} tool calls per turn.
5. Some tools are [GUARDIAN_GATED] — they will be safety-checked before execution.
6. When no tool is needed or your task is finished, respond normally with your final answer.

Context:
{memory_context}
"""


class BaseAgent:
    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        description: str,
        tools: list[str] | None = None,
        max_tool_steps: int = 5,
    ):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.tools = tools if tools is not None else []
        self.max_tool_steps = max_tool_steps

        # Register bindings in registry
        if self.tools:
            tool_registry.register_agent_tools(self.agent_type.value, self.tools)

    def _build_system_prompt(self, memory_context: str = "") -> str:
        if not self.tools:
            return f"System: You are {self.name} agent within C.O.P.P.E.R.\nDescription: {self.description}\nContext: {memory_context}"

        rendered_schemas = tool_registry.render_tool_schemas(self.tools)
        return SYSTEM_TOOL_TEMPLATE.format(
            name=self.name,
            description=self.description,
            rendered_tool_schemas=rendered_schemas,
            max_tool_steps=self.max_tool_steps,
            memory_context=memory_context or "None.",
        )

    def get_target_model(self) -> str:
        return ollama_client.select_model(self.agent_type)

    async def run(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        *args,
        **kwargs,
    ) -> str:
        if history is None:
            history = []

        system_prompt = self._build_system_prompt(memory_context)
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

        messages.append({"role": "user", "content": message})
        target_model = self.get_target_model()

        # If no tools, simple conversational invocation
        if not self.tools:
            try:
                res = await ollama_client.chat(messages, model=target_model, agent_type=self.agent_type)
                return res
            except Exception as e:
                logger.warning(f"Agent {self.name} fallback response: {e}")
                return f"[{self.name} Response]: Processed prompt '{message}'."

        # Tool-aware ReAct execution loop
        current_response = ""
        for step in range(self.max_tool_steps):
            try:
                current_response = await ollama_client.chat(
                    messages,
                    model=target_model,
                    agent_type=self.agent_type,
                )
            except Exception as e:
                logger.error(f"LLM chat error in agent {self.name} step {step + 1}: {e}")
                return f"[{self.name} Error]: {e}"

            tool_call = tool_executor.parse_tool_call(current_response)
            if not tool_call:
                # No more tool calls; return final text response
                return current_response

            # Validate tool belongs to agent or available tools
            if tool_call.tool not in self.tools and self.tools:
                logger.warning(f"Agent {self.name} requested unauthorized tool '{tool_call.tool}'")

            logger.info(f"Agent {self.name} executing tool '{tool_call.tool}' at step {step + 1}")
            result = await tool_executor.execute(
                tool_name=tool_call.tool,
                arguments=tool_call.arguments,
                context={"agent": self.name, "step": step + 1},
            )

            messages.append({"role": "assistant", "content": current_response})
            messages.append({"role": "user", "content": result.format_xml()})

        return current_response

    async def stream(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        *args,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        if history is None:
            history = []

        system_prompt = self._build_system_prompt(memory_context)
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

        messages.append({"role": "user", "content": message})

        target_model = self.get_target_model()
        metrics_collector = kwargs.get("metrics_collector")

        if not self.tools:
            async for chunk in ollama_client.stream_chat(
                messages, model=target_model, agent_type=self.agent_type, metrics_collector=metrics_collector
            ):
                yield chunk
            return

        for step in range(self.max_tool_steps):
            full_response = []
            async for chunk in ollama_client.stream_chat(
                messages, model=target_model, agent_type=self.agent_type, metrics_collector=metrics_collector
            ):
                full_response.append(chunk)
                yield chunk

            response_text = "".join(full_response)
            tool_call = tool_executor.parse_tool_call(response_text)
            if not tool_call:
                break

            yield f"\n\n⚙️ *Executing Tool:* `{tool_call.tool}`\n"
            result = await tool_executor.execute(
                tool_name=tool_call.tool,
                arguments=tool_call.arguments,
                context={"agent": self.name, "step": step + 1},
            )

            status_icon = "✅" if result.success else "❌"
            yield f"{status_icon} *Tool Observation Received.*\n\n"

            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": result.format_xml()})
