import pytest
from app.ai.agents.automation_agent import AutomationAgent
from app.ai.agents.base import BaseAgent
from app.ai.agents.coding_agent import CodingAgent
from app.ai.agents.reminder_agent import ReminderAgent
from app.ai.agents.research_agent import ResearchAgent
from app.ai.agents.vision_agent import VisionAgent
from app.core.constants import AgentType, LLMProvider


def test_base_agent_initialization():
    agent = BaseAgent(
        agent_type=AgentType.CHAT,
        name="Chat Core",
        description="General conversational agent",
    )
    assert agent.agent_type == AgentType.CHAT
    assert agent.name == "Chat Core"
    assert agent.description == "General conversational agent"


def test_coding_agent_attributes():
    agent = CodingAgent()
    assert agent.agent_type == AgentType.CODING
    assert "AXIS" in agent.name
    assert agent.description is not None


def test_automation_agent_attributes():
    agent = AutomationAgent()
    assert agent.agent_type == AgentType.AUTOMATION
    assert agent.name is not None
    assert agent.description is not None


def test_reminder_agent_attributes():
    agent = ReminderAgent()
    assert agent.agent_type == AgentType.REMINDER
    assert agent.name is not None


def test_research_agent_attributes():
    agent = ResearchAgent()
    assert agent.agent_type == AgentType.RESEARCH
    assert agent.name is not None


def test_vision_agent_attributes():
    agent = VisionAgent()
    assert agent.agent_type == AgentType.VISION
    assert agent.name is not None


@pytest.mark.asyncio
async def test_agent_fallback_execution():
    agent = BaseAgent(AgentType.CHAT, "TestAgent", "Unit test agent")
    response = await agent.run(
        message="Hello testing",
        history=[],
        memory_context="Context notes",
        provider=LLMProvider.OLLAMA,
    )
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_agent_streaming_generator():
    agent = BaseAgent(AgentType.RESEARCH, "Researcher", "Search and fact checking")
    stream = agent.stream(
        message="Explain relativity",
        history=[],
        memory_context="",
        provider=LLMProvider.OLLAMA,
    )
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)
    assert len(chunks) >= 1
    assert isinstance(chunks[0], str)
