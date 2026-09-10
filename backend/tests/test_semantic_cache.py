import asyncio
import time
import pytest
from fastapi.testclient import TestClient

from app.ai.cache.semantic_cache import SemanticResponseCache, semantic_cache
from app.main import app
from app.services.chat_service import chat_service


@pytest.fixture(autouse=True)
def reset_cache():
    asyncio.run(semantic_cache.clear())
    yield
    asyncio.run(semantic_cache.clear())


@pytest.mark.asyncio
async def test_cache_store_and_exact_hit():
    chash = semantic_cache.compute_context_hash("Python developer context", "2026-09-10")
    query = "What is Python list comprehension?"
    response = "List comprehension offers a shorter syntax when you want to create a new list."

    stored_id = await semantic_cache.store(
        query=query,
        response=response,
        agent_type="coding",
        context_hash=chash,
    )
    assert stored_id is not None

    # Exact match lookup
    res = await semantic_cache.lookup(query, context_hash=chash)
    assert res.status == "hit"
    assert res.cached_response == response
    assert res.similarity >= 0.95
    assert res.latency_ms < 10.0  # sub-millisecond to low ms


@pytest.mark.asyncio
async def test_cache_semantic_paraphrase_hit_and_dissimilar_miss():
    chash = semantic_cache.compute_context_hash("General context", "2026-09-10")
    query = "What is the capital of France?"
    response = "The capital of France is Paris."

    await semantic_cache.store(
        query=query,
        response=response,
        agent_type="chat",
        context_hash=chash,
    )

    # Paraphrased query lookup (high similarity)
    res_para = await semantic_cache.lookup("Tell me what the capital of France is", context_hash=chash)
    assert res_para.status == "hit"
    assert res_para.similarity >= 0.95
    assert res_para.cached_response == response

    # Completely dissimilar query lookup
    res_dissimilar = await semantic_cache.lookup("How to replace a car transmission?", context_hash=chash)
    assert res_dissimilar.status == "miss"
    assert res_dissimilar.similarity < 0.85


@pytest.mark.asyncio
async def test_cache_query_classification_and_ttl():
    # Time-sensitive: 1 hour (3600s)
    cat, ttl, is_ctx = semantic_cache.classify_query("What is today's stock price right now?")
    assert cat == "time_sensitive"
    assert ttl == SemanticResponseCache.TTL_TIME_SENSITIVE

    # Technical/Code: 7 days (604800s)
    cat, ttl, is_ctx = semantic_cache.classify_query("How to debug this python asyncio exception in fastapi?")
    assert cat == "code_technical"
    assert ttl == SemanticResponseCache.TTL_TECHNICAL

    # Context-dependent
    cat, ttl, is_ctx = semantic_cache.classify_query("What is my name and who am I?")
    assert is_ctx is True

    # Factual: 24 hours (86400s)
    cat, ttl, is_ctx = semantic_cache.classify_query("What is photosynthesis?")
    assert cat == "factual"
    assert ttl == SemanticResponseCache.TTL_FACTUAL


@pytest.mark.asyncio
async def test_cache_ttl_expiration_eviction():
    chash = semantic_cache.compute_context_hash("test")
    doc_id = await semantic_cache.store(
        query="What is the weather right now today?",
        response="It is sunny and 22 degrees.",
        agent_type="chat",
        context_hash=chash,
    )
    assert doc_id is not None

    # Simulate expired TTL by manipulating the timestamp in metadata
    entry = semantic_cache.collection.get(ids=[doc_id])
    meta = entry["metadatas"][0]
    meta["timestamp"] = time.time() - 4000  # Older than 3600s TTL
    semantic_cache.collection.update(ids=[doc_id], metadatas=[meta])
    semantic_cache._exact_cache.clear()

    # Expired query lookup must return miss and evict the item
    res = await semantic_cache.lookup("What is the weather right now today?", context_hash=chash)
    assert res.status == "miss"
    assert semantic_cache.collection.count() == 0


@pytest.mark.asyncio
async def test_context_aware_invalidation():
    # User memory changes
    chash_v1 = semantic_cache.compute_context_hash("User is Akash, a software engineer.")
    await semantic_cache.store(
        query="Who am I and what do I do?",
        response="You are Akash, a software engineer.",
        agent_type="chat",
        context_hash=chash_v1,
    )

    # Same context -> HIT
    res_hit = await semantic_cache.lookup("Who am I and what do I do?", context_hash=chash_v1)
    assert res_hit.status == "hit"

    # Memory context changed (e.g. user updated job) -> MISS
    chash_v2 = semantic_cache.compute_context_hash("User is Akash, a data scientist.")
    res_miss = await semantic_cache.lookup("Who am I and what do I do?", context_hash=chash_v2)
    assert res_miss.status == "miss"


def test_cache_api_stats_and_clear():
    client = TestClient(app)

    # Stats
    res_stats = client.get("/api/v1/cache/stats")
    assert res_stats.status_code == 200
    data = res_stats.json()
    assert data["status"] == "active"
    assert "hit_rate" in data
    assert "size" in data
    assert "avg_savings" in data

    # Clear
    res_clear = client.post("/api/v1/cache/clear")
    assert res_clear.status_code == 200
    clear_data = res_clear.json()
    assert clear_data["status"] == "success"
    assert "cleared_entries" in clear_data


@pytest.mark.asyncio
async def test_chat_service_instant_recall():
    session_id = "test-cache-session"
    prompt = "Explain quantum superposition in one sentence."
    response = "Quantum superposition is the principle that a system can exist in multiple states simultaneously."

    chash = semantic_cache.compute_context_hash()
    await semantic_cache.store(prompt, response, agent_type="chat", context_hash=chash)

    # process_message must detect cache hit BEFORE routing
    result = await chat_service.process_message(
        session_id=session_id,
        message=prompt,
    )

    assert result["response"] == response
    assert result["metrics"]["cached"] is True
    assert result["metrics"]["instant_recall"] is True
    assert result["metrics"]["model"] == "cache:instant-recall"
    assert result["metrics"]["total_time_ms"] < 5.0
