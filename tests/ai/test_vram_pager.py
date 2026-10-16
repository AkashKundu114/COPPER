"""Tests for VRAM Pager & Dynamic Model Swapper."""

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

    res1 = await pager.acquire_model("mistral:7b")
    assert res1 is True
    assert pager.stats["cold_loads"] == 1
    assert pager.stats["cache_hits"] == 0

    res2 = await pager.acquire_model("mistral:7b")
    assert res2 is True
    assert pager.stats["cache_hits"] == 1
    assert pager._pages["mistral:7b"].access_count == 2


@pytest.mark.asyncio
async def test_vram_pager_eviction_when_exceeding_capacity():
    pager = VRAMPager(vram_capacity_gb=8.0, pinned_gatekeeper="qwen2.5:1.5b")

    await pager.acquire_model("llama3.1:8b")
    assert pager.is_resident("llama3.1:8b")
    assert pager.is_resident("qwen2.5:1.5b")

    await pager.acquire_model("deepseek-r1:7b")
    assert pager.is_resident("deepseek-r1:7b")
    assert pager.is_resident("qwen2.5:1.5b")
    assert not pager.is_resident("llama3.1:8b")
    assert pager.stats["evictions"] == 1


@pytest.mark.asyncio
async def test_vram_pager_dag_lookahead_protects_upcoming_model():
    pager = VRAMPager(vram_capacity_gb=10.0, pinned_gatekeeper="qwen2.5:1.5b")

    await pager.acquire_model("mistral:7b")
    await pager.acquire_model("qwen2.5-coder:7b")

    pager.update_dag_lookahead([("mistral:7b", 0.95)])

    await pager.acquire_model("deepseek-r1:7b")

    assert pager.is_resident("mistral:7b")
    assert not pager.is_resident("qwen2.5-coder:7b")
    assert pager.is_resident("deepseek-r1:7b")


@pytest.mark.asyncio
async def test_vram_pager_telemetry_metrics():
    pager = VRAMPager(vram_capacity_gb=16.0, pinned_gatekeeper="qwen2.5:1.5b")
    await pager.acquire_model("mistral:7b")
    await pager.acquire_model("mistral:7b")

    telemetry = pager.get_telemetry()
    assert telemetry["capacity_gb"] == 16.0
    assert "allocated_vram_gb" in telemetry
    assert "available_vram_gb" in telemetry
    assert telemetry["stats"]["total_requests"] == 2
    assert telemetry["stats"]["cache_hits"] == 1
    assert telemetry["stats"]["hit_ratio_pct"] == 50.0
