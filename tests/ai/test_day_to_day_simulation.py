import pytest

from app.ai.memory.persistent_memory import persistent_memory
from app.ai.orchestration.agent_router import route_message_detailed
from app.core.constants import AgentType
from app.services.chat_service import chat_service
from app.services.directive_service import directive_service


@pytest.mark.asyncio
async def test_day_to_day_morning_checkin_and_identity():
    """Day-to-day Scenario 1: Morning Check-in."""
    prompt = "Good morning COPPER, who am I and what do I do?"
    route = await route_message_detailed(prompt)
    assert route.agent == AgentType.CHAT

    model = chat_service._resolve_chat_model(route.agent, prompt)
    assert any(tag in model.lower() for tag in ["1b", "1.5b", "mini"])

    snippet = persistent_memory.get_memory_prompt_snippet()
    assert "Akash" in snippet
    assert "Software Engineer" in snippet


@pytest.mark.asyncio
async def test_day_to_day_model_directives_and_switching():
    """Day-to-day Scenario 2: Model Sizing Control via Natural Language."""
    res1 = await directive_service.evaluate("use a smaller model to talk with me")
    assert res1.is_directive is True
    assert res1.action == "set_chat_model"
    assert "1b" in persistent_memory.get_chat_model().lower() or "mini" in persistent_memory.get_chat_tier().lower()

    resolved_model = chat_service._resolve_chat_model(AgentType.CHAT, "whats my age")
    assert any(tag in resolved_model.lower() for tag in ["1b", "1.5b", "mini"])

    res_3b = await directive_service.evaluate("switch to 3b model")
    assert res_3b.is_directive is True
    assert "3b" in persistent_memory.get_chat_model().lower()

    res_8b = await directive_service.evaluate("switch back to 8b model")
    assert res_8b.is_directive is True
    assert "8b" in persistent_memory.get_chat_model().lower()

    await directive_service.evaluate("reset model")
    assert persistent_memory.get_chat_model() is None


@pytest.mark.asyncio
async def test_day_to_day_task_and_reminder_scheduling():
    """Day-to-day Scenario 3: Task & Reminder Management."""
    prompt = "Remind me to review the pull request tomorrow at 4 PM"
    route = await route_message_detailed(prompt)
    assert route.agent == AgentType.REMINDER
    assert route.confidence >= 0.70


@pytest.mark.asyncio
async def test_day_to_day_software_engineering_workflow():
    """Day-to-day Scenario 4: Software Architecture & Code Generation."""
    prompt = "Write a python function to compute exponential moving average using numpy"
    route = await route_message_detailed(prompt)
    assert route.agent == AgentType.CODING
    assert route.confidence >= 0.70


@pytest.mark.asyncio
async def test_day_to_day_document_generation_workflow():
    """Day-to-day Scenario 5: Document Generation & Reporting."""
    prompt = "Generate a markdown technical report on SQLite performance optimization"
    route = await route_message_detailed(prompt)
    assert route.agent == AgentType.DOCUMENT
    assert route.confidence >= 0.70


@pytest.mark.asyncio
async def test_day_to_day_voice_and_audio_customization():
    """Day-to-day Scenario 6: Voice & Hands-Free Audio Customization."""
    res_voice = await directive_service.evaluate("change voice to Jenny")
    assert res_voice.is_directive is True
    assert persistent_memory.get_preference("voice") == "en-US-JennyNeural"

    res_hf = await directive_service.evaluate("enable hands-free mode")
    assert res_hf.is_directive is True
    assert persistent_memory.get_preference("continuous_voice") is True

    await directive_service.evaluate("change voice to Ava")
    assert persistent_memory.get_preference("voice") == "en-US-AvaNeural"


@pytest.mark.asyncio
async def test_day_to_day_vram_and_resource_discipline():
    """Day-to-day Scenario 7: Resource Management & VRAM Flushing."""
    res = await directive_service.evaluate("clear vram")
    assert res.is_directive is True
    assert res.action == "unload_vram"
    assert "VRAM PURGE" in res.confirmation
