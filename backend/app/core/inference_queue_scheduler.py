"""Residency-Aware Queue Scheduler & Model Affinity Dispatcher for C.O.P.P.E.R.

Optimizes local inference scheduling by promoting tasks whose target model
is already warm and resident in VRAM, eliminating unnecessary model unload/reload cycles.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.ai.llm.vram_pager import vram_pager
from app.core.logger import logger


@dataclass(order=True)
class ScheduledInferenceRequest:
    effective_priority: float  # Lower value = higher execution priority
    task_id: str = field(compare=False)
    target_model: str = field(compare=False)
    base_priority: int = field(compare=False)  # 0=CRITICAL, 1=HIGH, 2=NORMAL, 3=BACKGROUND
    enqueued_at: float = field(compare=False, default_factory=time.time)
    residency_boost_applied: bool = field(compare=False, default=False)
    context: dict[str, Any] = field(compare=False, default_factory=dict)


class ResidencyAwareScheduler:
    """Dispatches inference tasks favoring warm model locality."""

    def __init__(self, residency_boost_weight: float = 0.85):
        self.residency_boost_weight = residency_boost_weight

    def calculate_priority(self, base_priority: int, target_model: str) -> tuple[float, bool]:
        """Calculates effective priority with VRAM residency affinity.
        
        If target_model is already resident in VRAM, priority is boosted by subtracting
        residency_boost_weight from effective priority score.
        """
        is_warm = vram_pager.is_resident(target_model)
        boost = self.residency_boost_weight if is_warm else 0.0
        # Effective priority combines base tier with residency bonus
        effective_prio = round(float(base_priority) - boost, 3)
        return effective_prio, is_warm

    def schedule_request(
        self,
        task_id: str,
        target_model: str,
        base_priority: int = 2,
        context: dict[str, Any] | None = None,
    ) -> ScheduledInferenceRequest:
        eff_prio, is_warm = self.calculate_priority(base_priority, target_model)
        if is_warm:
            logger.debug(
                f"[ResidencyScheduler] Applied zero-switch boost to task {task_id} "
                f"for warm model '{target_model}' (Effective priority: {eff_prio:.2f})"
            )
        return ScheduledInferenceRequest(
            effective_priority=eff_prio,
            task_id=task_id,
            target_model=target_model,
            base_priority=base_priority,
            residency_boost_applied=is_warm,
            context=context or {},
        )

    def sort_task_batch_by_affinity(
        self,
        tasks: list[ScheduledInferenceRequest],
    ) -> list[ScheduledInferenceRequest]:
        """Groups and orders a batch of subtasks to minimize cold model swaps."""
        # Primary sort: effective priority (residency-boosted)
        # Secondary sort: group by target_model
        return sorted(tasks, key=lambda t: (t.effective_priority, t.target_model, t.enqueued_at))


residency_aware_scheduler = ResidencyAwareScheduler()
