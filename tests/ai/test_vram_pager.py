"""
Tests for VRAM Pager & Dynamic Model Swapper.
Verifies weighted LRU eviction, DAG lookahead priority, gatekeeper pinning, and telemetry.
"""

import pytest

from app.ai.llm.vram_pager import VRAMPager


@pytest.mark.asyncio
async def test_vram_pager_initialization_pins_gatekeeper():
    pager = VRAMPager(vram_capacity_gb=8.0, pinned_gatekeeper="qwen2.5:1.5b")
    assert pager.is_resident("qwen2.5:1.5b")
    page = pager._pages["qwen2.5:1.5b"]
    assert page.is_pinned is True
    assert pager.current_allocated_vram_gb == page.vram_gb


@pytest.mark.asyncio
async def test_vram_pager_cache_hit_and_access_tracking():
    pager = VRAMPager(vram_capacity_gb=12.0, pinned_gatekeeper="qwen2.5:1.5b")

    # First access: cold load
    res1 = await pager.acquire_model("mistral:7b")
    assert res1 is True
    assert pager.stats["cold_loads"] == 1
    assert pager.stats["cache_hits"] == 0

    # Second access: cache hit
    res2 = await pager.acquire_model("mistral:7b")
    assert res2 is True
    assert pager.stats["cache_hits"] == 1
    assert pager._pages["mistral:7b"].access_count == 2


@pytest.mark.asyncio
async def test_vram_pager_eviction_when_exceeding_capacity():
    # Set tight capacity: 8 GB. Gatekeeper uses 1.2 GB.
    # llama3.1:8b uses 4.8 GB. Total = 6.0 GB (fits).
    # Next, deepseek-r1:7b uses 4.5 GB. 6.0 + 4.5 = 10.5 GB > 8.0 GB -> must evict llama3.1:8b!
    pager = VRAMPager(vram_capacity_gb=8.0, pinned_gatekeeper="qwen2.5:1.5b")

    await pager.acquire_model("llama3.1:8b")
    assert pager.is_resident("llama3.1:8b")
    assert pager.is_resident("qwen2.5:1.5b")

    # Load second heavy model
    await pager.acquire_model("deepseek-r1:7b")
    assert pager.is_resident("deepseek-r1:7b")
    # Gatekeeper must NEVER be evicted
    assert pager.is_resident("qwen2.5:1.5b")
    # llama3.1:8b should have been evicted
    assert not pager.is_resident("llama3.1:8b")
    assert pager.stats["evictions"] == 1


@pytest.mark.asyncio
async def test_vram_pager_dag_lookahead_protects_upcoming_model():
    # Capacity 10 GB. Pinned gatekeeper (1.2 GB).
    pager = VRAMPager(vram_capacity_gb=10.0, pinned_gatekeeper="qwen2.5:1.5b")

    await pager.acquire_model("mistral:7b")  # 4.2 GB
    await pager.acquire_model("qwen2.5-coder:7b")  # 4.4 GB
    # Total = 1.2 + 4.2 + 4.4 = 9.8 GB (nearly full)

    # Invert priority: mistral has lower frequency, but DAG scheduler predicts it is needed next!
    pager.update_dag_lookahead([("mistral:7b", 0.95)])

    # Now load deepseek-r1 (4.5 GB) -> one model MUST be evicted.
    # mistral was protected by DAG lookahead, so qwen2.5-coder:7b should be evicted!
    await pager.acquire_model("deepseek-r1:7b")

    assert pager.is_resident("mistral:7b")
    assert not pager.is_resident("qwen2.5-coder:7b")
    assert pager.is_resident("deepseek-r1:7b")


@pytest.mark.asyncio
async def test_vram_pager_telemetry_metrics():
    pager = VRAMPager(vram_capacity_gb=16.0, pinned_gatekeeper="qwen2.5:1.5b")
    await pager.acquire_model("mistral:7b")
    await pager.acquire_model("mistral:7b")  # Hit

    telemetry = pager.get_telemetry()
    assert telemetry["capacity_gb"] == 16.0
    assert "allocated_vram_gb" in telemetry
    assert "available_vram_gb" in telemetry
    assert telemetry["stats"]["total_requests"] == 2
    assert telemetry["stats"]["cache_hits"] == 1
    assert telemetry["stats"]["hit_ratio_pct"] == 50.0
