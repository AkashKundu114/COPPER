import pytest
from app.ai.memory.persistent_memory import persistent_memory
from app.core.constants import AgentType
from app.services.chat_service import chat_service
from app.services.directive_service import directive_service


@pytest.mark.asyncio
async def test_directive_smaller_model():
    res = await directive_service.evaluate("use a smaller model to talk with me")
    assert res.is_directive is True
    assert res.action == "set_chat_model"
    assert "Mini" in res.updates.get("tier_name", "")
    assert persistent_memory.get_chat_model() is not None
    assert "1b" in persistent_memory.get_chat_model().lower() or "mini" in persistent_memory.get_chat_tier().lower()


@pytest.mark.asyncio
async def test_directive_specific_sizes():
    # 3B model
    res_3b = await directive_service.evaluate("switch to 3b model")
    assert res_3b.is_directive is True
    assert "3b" in res_3b.updates.get("chat_model", "").lower()
    assert persistent_memory.get_chat_model() == res_3b.updates.get("chat_model")

    # 8B model
    res_8b = await directive_service.evaluate("switch back to 8b model")
    assert res_8b.is_directive is True
    assert "8b" in res_8b.updates.get("chat_model", "").lower()
    assert persistent_memory.get_chat_model() == res_8b.updates.get("chat_model")


@pytest.mark.asyncio
async def test_directive_reset_model():
    res = await directive_service.evaluate("reset model")
    assert res.is_directive is True
    assert res.action == "reset_model"
    assert persistent_memory.get_chat_model() is None


@pytest.mark.asyncio
async def test_directive_voice_engine():
    res = await directive_service.evaluate("change voice to Jenny")
    assert res.is_directive is True
    assert res.action == "set_voice"
    assert "Jenny" in res.updates.get("voice_name", "")
    assert persistent_memory.get_preference("voice") == "en-US-JennyNeural"


@pytest.mark.asyncio
async def test_directive_hands_free():
    res = await directive_service.evaluate("enable hands-free mode")
    assert res.is_directive is True
    assert persistent_memory.get_preference("continuous_voice") is True

    res_off = await directive_service.evaluate("disable hands-free mode")
    assert res_off.is_directive is True
    assert persistent_memory.get_preference("continuous_voice") is False


@pytest.mark.asyncio
async def test_directive_cognitive_mode():
    res = await directive_service.evaluate("switch to reasoning mode")
    assert res.is_directive is True
    assert res.action == "set_cognitive_mode"
    assert persistent_memory.get_cognitive_mode() == "reasoning"


@pytest.mark.asyncio
async def test_compound_directive_and_question():
    res = await directive_service.evaluate("use a smaller model and tell me my age")
    assert res.is_directive is True
    assert res.action == "set_chat_model"
    assert res.remaining_prompt == "tell me my age"


@pytest.mark.asyncio
async def test_chat_service_resolves_preferred_model():
    # When user ordered a smaller model:
    await directive_service.evaluate("use a smaller model")
    resolved = chat_service._resolve_chat_model(AgentType.CHAT, "whats my age")
    assert "1b" in resolved.lower() or "mini" in resolved.lower()

    # When user reset model, adaptive intent for "whats my age" still picks fast mini model:
    await directive_service.evaluate("reset model")
    adaptive_resolved = chat_service._resolve_chat_model(AgentType.CHAT, "whats my age")
    assert "1b" in adaptive_resolved.lower()

    # Complex conversation without preference picks 8B:
    complex_resolved = chat_service._resolve_chat_model(
        AgentType.CHAT,
        "can you provide an in-depth philosophical treatise on the epistemology of synthetic neural architectures?",
    )
    assert "8b" in complex_resolved.lower()
