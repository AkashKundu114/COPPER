"""VRAM Pager & Dynamic Model Swapper."""

import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import settings
from app.core.logger import logger

MODEL_VRAM_ESTIMATES: dict[str, float] = {
    "qwen2.5:14b": 6.38,
    "qwen2.5-14b-instruct": 6.38,
    "qwen2.5-coder-abliterated:14b": 6.38,
    "qwen2.5-coder:14b": 6.38,
    "deepseek-r1:14b": 6.38,
    "deepseek-r1-distill-qwen-14b": 6.38,
    "phi4:14b": 6.24,
    "phi-4": 6.24,
    "mistral-nemo:12b": 5.72,
    "mistral-nemo-instruct-2407": 5.72,
    "qwen2.5-vl:3b": 2.10,
    "qwen2.5-vl-3b-instruct": 2.10,
    "sd_turbo": 4.86,
    "qwen2.5-coder:3b": 1.80,
    "granite3.2-dense:2b": 1.44,
    "granite-3.2-2b-instruct": 1.44,
    "qwen2.5:1.5b": 0.94,
    "qwen2.5-1.5b-instruct": 0.94,
    "deepseek-r1:1.5b": 1.04,
    "deepseek-r1-distill-qwen-1.5b": 1.04,
    "smollm2:1.7b": 1.00,
    "smollm2-1.7b-instruct": 1.00,
    "smollm2:360m": 0.36,
    "qwen2.5:0.5b": 0.45,
    "nomic-embed-text": 0.14,
    "bge-reranker-v2-m3": 0.32,
    "llama3.1:8b": 4.80,
    "mistral:7b": 4.20,
    "qwen2.5-coder:7b": 4.40,
}

DEFAULT_FALLBACK_VRAM_GB: float = 4.2


@dataclass
class ModelPage:
    name: str
    vram_gb: float
    is_pinned: bool = False
    loaded_at: float = field(default_factory=time.time)
    last_accessed_at: float = field(default_factory=time.time)
    access_count: int = 1
    lookahead_priority: float = 0.0

    def compute_priority_score(self, current_time: float) -> float:
        """Higher score = higher priority to STAY in VRAM."""
        if self.is_pinned:
            return float("inf")

        idle_seconds = max(0.0, current_time - self.last_accessed_at)
        recency = 1.0 / (1.0 + (idle_seconds / 60.0))

        frequency = min(1.0, self.access_count / 10.0)

        lookahead = max(0.0, min(1.0, self.lookahead_priority))

        return (0.40 * recency) + (0.20 * frequency) + (0.40 * lookahead)


class VRAMPager:
    """Virtual Memory Pager for Local LLM Instances."""

    def __init__(
        self,
        vram_capacity_gb: float = 8.0,
        pinned_gatekeeper: str = "qwen2.5:1.5b",
    ):
        self.capacity_gb: float = vram_capacity_gb
        self.pinned_model: str = pinned_gatekeeper
        self._pages: dict[str, ModelPage] = {}
        self._base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")

        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cold_loads": 0,
            "evictions": 0,
            "preemptions": 0,
        }

        self._pin_gatekeeper(pinned_gatekeeper)

    def _pin_gatekeeper(self, model_name: str) -> None:
        footprint = self.estimate_vram(model_name)
        self._pages[model_name] = ModelPage(
            name=model_name,
            vram_gb=footprint,
            is_pinned=True,
            lookahead_priority=1.0,
        )

    def estimate_vram(self, model_name: str) -> float:
        clean = model_name.lower().strip()
        for k, v in MODEL_VRAM_ESTIMATES.items():
            if k in clean or clean in k:
                return v
        return DEFAULT_FALLBACK_VRAM_GB

    @property
    def current_allocated_vram_gb(self) -> float:
        return sum(page.vram_gb for page in self._pages.values())

    @property
    def available_vram_gb(self) -> float:
        return max(0.0, self.capacity_gb - self.current_allocated_vram_gb)

    def is_resident(self, model_name: str) -> bool:
        return model_name in self._pages

    async def acquire_model(self, model_name: str, lookahead_priority: float = 0.0) -> bool:
        """Request model residency. If already resident, updates LRU metadata (cache hit)."""
        self.stats["total_requests"] += 1
        now = time.time()

        if model_name in self._pages:
            page = self._pages[model_name]
            page.last_accessed_at = now
            page.access_count += 1
            page.lookahead_priority = max(page.lookahead_priority, lookahead_priority)
            self.stats["cache_hits"] += 1
            return True

        self.stats["cold_loads"] += 1
        required_vram = self.estimate_vram(model_name)

        while self.available_vram_gb < required_vram:
            evicted = await self._evict_lowest_priority()
            if not evicted:
                logger.warning(
                    f"[VRAMPager] Insufficient VRAM headroom ({self.available_vram_gb:.2f} GB) "
                    f"for {model_name} ({required_vram:.2f} GB). Pushing with overcommit."
                )
                break

        self._pages[model_name] = ModelPage(
            name=model_name,
            vram_gb=required_vram,
            is_pinned=(model_name == self.pinned_model),
            loaded_at=now,
            last_accessed_at=now,
            lookahead_priority=lookahead_priority,
        )
        return True

    async def _evict_lowest_priority(self) -> bool:
        """Finds and evicts the model page with lowest priority score."""
        now = time.time()
        evictable = [p for p in self._pages.values() if not p.is_pinned]
        if not evictable:
            return False

        evictable.sort(key=lambda p: p.compute_priority_score(now))
        victim = evictable[0]

        logger.info(
            f"[VRAMPager] Evicting model '{victim.name}' "
            f"(VRAM: {victim.vram_gb:.2f} GB, idle: {now - victim.last_accessed_at:.1f}s)"
        )

        await self._unload_ollama_model(victim.name)
        self._pages.pop(victim.name, None)
        self.stats["evictions"] += 1
        return True

    async def _unload_ollama_model(self, model_name: str) -> None:
        try:
            timeout = httpx.Timeout(1.0, connect=0.25)
            async with httpx.AsyncClient(timeout=timeout) as client:
                await client.post(
                    f"{self._base_url}/api/chat",
                    json={"model": model_name, "keep_alive": 0},
                )
        except Exception as e:
            logger.debug(f"[VRAMPager] Ollama unload API notification failed for {model_name}: {e}")

    def update_dag_lookahead(self, upcoming_models: list[tuple[str, float]]) -> None:
        """Called by DAG Task Scheduler. Injects lookahead priority weights"""
        for model_name, priority in upcoming_models:
            if model_name in self._pages:
                self._pages[model_name].lookahead_priority = priority
            self.stats["preemptions"] += 1

    def get_telemetry(self) -> dict[str, Any]:
        """Provides real-time systems telemetry for interview demo and monitoring."""
        now = time.time()
        hit_ratio = self.stats["cache_hits"] / self.stats["total_requests"] if self.stats["total_requests"] > 0 else 1.0
        return {
            "capacity_gb": self.capacity_gb,
            "allocated_vram_gb": round(self.current_allocated_vram_gb, 2),
            "available_vram_gb": round(self.available_vram_gb, 2),
            "utilization_pct": round((self.current_allocated_vram_gb / max(1.0, self.capacity_gb)) * 100, 1),
            "resident_models": [
                {
                    "name": p.name,
                    "vram_gb": p.vram_gb,
                    "is_pinned": p.is_pinned,
                    "idle_seconds": round(now - p.last_accessed_at, 1),
                    "access_count": p.access_count,
                    "priority_score": round(p.compute_priority_score(now), 4),
                }
                for p in self._pages.values()
            ],
            "stats": {
                **self.stats,
                "hit_ratio_pct": round(hit_ratio * 100, 1),
            },
        }


vram_pager = VRAMPager()
