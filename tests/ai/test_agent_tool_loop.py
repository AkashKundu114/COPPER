from unittest.mock import AsyncMock, patch
import pytest

from app.ai.agents.base import BaseAgent
from app.ai.agents.coding_agent import coding_agent
from app.ai.agents.automation_agent import automation_agent
from app.ai.agents.research_agent import research_agent
from app.ai.agents.reminder_agent import reminder_agent
from app.core.constants import AgentType


def test_agent_tool_configuration():
    assert "python_execute" in coding_agent.tools
    assert "shell_execute" in coding_agent.tools
    assert "file_read" in coding_agent.tools

    assert "shell_execute" in automation_agent.tools
    assert "file_write" in automation_agent.tools

    assert "web_search" in research_agent.tools
    assert "memory_query" in research_agent.tools

    assert "calendar_create" in reminder_agent.tools
    assert "reminder_set" in reminder_agent.tools


@pytest.mark.asyncio
async def test_agent_tool_react_loop():
    agent = BaseAgent(
        agent_type=AgentType.CODING,
        name="TestCoder",
        description="Coding test agent",
        tools=["python_execute"],
        max_tool_steps=3,
    )

    # Mock Ollama chat to return a tool call on step 1 and final response on step 2
    step1_response = """Let me calculate that for you.
<tool_call>
{"tool": "python_execute", "arguments": {"code": "print(2 + 2)"}}
</tool_call>"""

    step2_response = "The calculation result is 4."

    with patch("app.ai.llm.ollama_client.ollama_client.chat", side_effect=[step1_response, step2_response]):
        final_answer = await agent.run(
            message="Calculate 2 + 2",
            history=[],
            memory_context="",
        )

        assert "The calculation result is 4." in final_answer


@pytest.mark.asyncio
async def test_agent_direct_response_without_tools():
    agent = BaseAgent(
        agent_type=AgentType.CHAT,
        name="TestChat",
        description="Chat test agent",
        tools=[],
    )

    with patch("app.ai.llm.ollama_client.ollama_client.chat", return_value="Hello there!"):
        res = await agent.run("Hi", history=[], memory_context="")
        assert res == "Hello there!"
