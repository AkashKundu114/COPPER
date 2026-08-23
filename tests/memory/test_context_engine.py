import pytest
from app.ai.memory.context_engine import ContextEngine, context_engine


def test_context_engine_instance():
    assert context_engine is not None
    assert isinstance(context_engine, ContextEngine)


@pytest.mark.asyncio
async def test_context_engine_empty_session():
    sid = "ctx_test_session_empty"
    await context_engine.clear_session(sid)
    hist = await context_engine.get_history(sid)
    assert len(hist) == 0


@pytest.mark.asyncio
async def test_context_engine_append_single():
    sid = "ctx_test_session_1"
    await context_engine.clear_session(sid)
    await context_engine.append_message(sid, "user", "Message A")
    hist = await context_engine.get_history(sid)
    assert len(hist) == 1
    assert hist[0]["content"] == "Message A"


@pytest.mark.asyncio
async def test_context_engine_multi_turn():
    sid = "ctx_test_session_multi"
    await context_engine.clear_session(sid)
    await context_engine.append_message(sid, "user", "Turn 1")
    await context_engine.append_message(sid, "assistant", "Response 1")
    await context_engine.append_message(sid, "user", "Turn 2")
    hist = await context_engine.get_history(sid)
    assert len(hist) == 3


@pytest.mark.asyncio
async def test_context_engine_build_context():
    sid = "ctx_test_session_build"
    await context_engine.clear_session(sid)
    await context_engine.append_message(sid, "user", "How do I build RAG?")
    history, mem = await context_engine.build_context(sid, "How do I build RAG?")
    assert len(history) == 1
    assert isinstance(mem, str)


@pytest.mark.asyncio
async def test_context_engine_clear():
    sid = "ctx_test_session_clear"
    await context_engine.append_message(sid, "user", "Temporary")
    await context_engine.clear_session(sid)
    hist = await context_engine.get_history(sid)
    assert len(hist) == 0
