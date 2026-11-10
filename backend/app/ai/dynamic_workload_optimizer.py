"""Adaptive Runtime Workload & Dynamic Model Unloading Optimizer for C.O.P.P.E.R.

Dynamically manages resident model life cycles, automates model unloading upon
idle timeouts, enforces memory reclamation, and optimizes context reuse while
asserting strict compliance with the host 8.0 GB VRAM boundary.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.ai.llm.quantization_vram import quantization_vram_estimator
from app.core.logger import logger


@dataclass
class ResidentModelSlot:
    model_name: str
    vram_allocated_gb: float
    loaded_at: float
    last_accessed: float
    is_pinned: bool = False  # e.g., Gatekeeper model is permanently pinned


@dataclass
class WorkloadOptimizationReport:
    report_id: str
    timestamp: float
    hardware_vram_limit_gb: float
    total_resident_vram_gb: float
    resident_models: list[str]
    evicted_models_count: int
    vram_safe: bool
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DynamicWorkloadOptimizer:
    """Manages dynamic VRAM allocation, residency hot-swapping, and idle evictions."""

    HARDWARE_VRAM_LIMIT_GB: float = 8.0

    def __init__(self, idle_timeout_seconds: float = 120.0):
        self.idle_timeout_seconds = idle_timeout_seconds
        self._slots: dict[str, ResidentModelSlot] = {}
        self._eviction_count: int = 0

        # Pin default gatekeeper model
        self.load_model("qwen2.5:1.5b", is_pinned=True)

    def load_model(self, model_name: str, is_pinned: bool = False) -> tuple[bool, str]:
        """Loads a model into resident memory, evicting idle unpinned models if needed to fit in 8GB."""
        footprint = quantization_vram_estimator.estimate_vram(model_name)
        needed_gb = footprint.total_vram_gb

        if needed_gb > self.HARDWARE_VRAM_LIMIT_GB:
            return False, f"Model '{model_name}' requires {needed_gb:.2f}GB VRAM, exceeding 8.0 GB hardware budget."

        # If already resident, touch last_accessed
        if model_name in self._slots:
            self._slots[model_name].last_accessed = time.time()
            return True, f"Model '{model_name}' is already resident."

        # Evict unpinned idle models if needed to free VRAM
        curr_vram = sum(s.vram_allocated_gb for s in self._slots.values())
        while (curr_vram + needed_gb) > self.HARDWARE_VRAM_LIMIT_GB:
            evicted = self._evict_oldest_unpinned_model()
            if not evicted:
                return False, "Cannot allocate VRAM: All resident models are pinned or active."
            curr_vram = sum(s.vram_allocated_gb for s in self._slots.values())

        now = time.time()
        self._slots[model_name] = ResidentModelSlot(
            model_name=model_name,
            vram_allocated_gb=round(needed_gb, 2),
            loaded_at=now,
            last_accessed=now,
            is_pinned=is_pinned,
        )
        logger.info(f"[DynamicWorkloadOptimizer] Loaded model '{model_name}' ({needed_gb:.2f}GB VRAM)")
        return True, "Loaded successfully"

    def _evict_oldest_unpinned_model(self) -> str | None:
        """Evicts the least recently used unpinned model."""
        candidates = [s for s in self._slots.values() if not s.is_pinned]
        if not candidates:
            return None

        oldest = min(candidates, key=lambda s: s.last_accessed)
        del self._slots[oldest.model_name]
        self._eviction_count += 1
        logger.info(f"[DynamicWorkloadOptimizer] Evicted idle model '{oldest.model_name}' ({oldest.vram_allocated_gb}GB freed)")
        return oldest.model_name

    def evict_idle_models(self) -> int:
        """Evicts any unpinned models exceeding the idle timeout."""
        now = time.time()
        to_evict = [
            s.model_name
            for s in self._slots.values()
            if not s.is_pinned and (now - s.last_accessed) >= self.idle_timeout_seconds
        ]
        for m in to_evict:
            del self._slots[m]
            self._eviction_count += 1
            logger.info(f"[DynamicWorkloadOptimizer] Idle eviction triggered for '{m}'")
        return len(to_evict)

    def generate_optimization_report(self) -> WorkloadOptimizationReport:
        """Generates dynamic VRAM allocation and optimization status report."""
        now = time.time()
        total_vram = sum(s.vram_allocated_gb for s in self._slots.values())
        vram_ok = total_vram <= self.HARDWARE_VRAM_LIMIT_GB

        rep_id = f"OPT-REP-{hashlib.sha256(str(now).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{rep_id}:{total_vram}:{vram_ok}".encode()).hexdigest()

        report = WorkloadOptimizationReport(
            report_id=rep_id,
            timestamp=now,
            hardware_vram_limit_gb=self.HARDWARE_VRAM_LIMIT_GB,
            total_resident_vram_gb=round(total_vram, 2),
            resident_models=list(self._slots.keys()),
            evicted_models_count=self._eviction_count,
            vram_safe=vram_ok,
            signature=sig,
        )

        logger.info(
            f"[DynamicWorkloadOptimizer] Optimization report: {total_vram:.2f}GB / 8.0GB "
            f"(Resident: {list(self._slots.keys())}, VRAM Safe={vram_ok})"
        )
        return report


dynamic_workload_optimizer = DynamicWorkloadOptimizer()
