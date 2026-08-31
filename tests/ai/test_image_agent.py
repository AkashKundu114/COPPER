import pytest
from app.ai.agents.image_agent import ImageAgent, image_agent
from app.core.constants import AgentType, LLMProvider


def test_image_agent_initialization():
    agent = ImageAgent()
    assert agent.agent_type == AgentType.IMAGE
    assert "PICASSO" in agent.name
    assert agent.description is not None
    assert agent.output_dir is not None


def test_extract_prompt_variations():
    agent = ImageAgent()

    assert agent.extract_prompt("generate an image of a neon cyber city") == "neon cyber city"
    assert agent.extract_prompt("draw a picture of an astronaut on Mars") == "astronaut on Mars"
    assert agent.extract_prompt("create an image of a copper mechanical owl") == "copper mechanical owl"
    assert agent.extract_prompt("make a photo of a cozy cabin in the rain") == "cozy cabin in the rain"
    assert agent.extract_prompt("draw me a robotic dragon") == "robotic dragon"
    assert agent.extract_prompt("draw a futuristic sports car") == "futuristic sports car"
    assert agent.extract_prompt("generate a wallpaper of synthwave mountains") == "wallpaper of synthwave mountains"


def test_extract_prompt_fallback():
    agent = ImageAgent()
    assert agent.extract_prompt("generate") == ""
    assert agent.extract_prompt("draw") == ""


@pytest.mark.asyncio
async def test_image_agent_run():
    agent = ImageAgent()
    result = await agent.run(
        message="generate an image of a copper robot",
        history=[],
        memory_context="",
        provider=LLMProvider.OLLAMA,
    )
    assert isinstance(result, str)
    assert "🎨 **Generated Image for:**" in result
    assert "pollinations.ai" in result
    assert "copper%20robot" in result or "copper+robot" in result


@pytest.mark.asyncio
async def test_image_agent_empty_prompt_fallback():
    agent = ImageAgent()
    result = await agent.run(
        message="draw",
        history=[],
        memory_context="",
        provider=LLMProvider.OLLAMA,
    )
    assert "a futuristic cyber city" in result


@pytest.mark.asyncio
async def test_image_agent_streaming():
    agent = ImageAgent()
    stream = agent.stream("draw a neon tiger")
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)

    assert len(chunks) == 1
    assert "neon tiger" in chunks[0]
    assert "pollinations.ai" in chunks[0]


def test_singleton_instance():
    assert image_agent is not None
    assert isinstance(image_agent, ImageAgent)
