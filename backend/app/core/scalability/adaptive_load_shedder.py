"""Adaptive Priority-Weighted Load Shedder and CoDel Queue Manager.

Implements Stage 9 Scalability Architecture:
- Implements Controlled Delay (CoDel) queuing principles to eliminate bufferbloat.
- Drops speculative or low-priority background workloads during queue saturation.
- Guarantees VIP and user-facing interactive inference SLA compliance under extreme load.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional


class WorkloadPriority(IntEnum):
    BACKGROUND = 1
    SPECULATIVE = 2
    STANDARD = 3
    CRITICAL_USER = 4


@dataclass
class QueuedTask:
    task_id: str
    priority: WorkloadPriority
    enqueued_at: float
    payload: dict[str, Any]
    sojourn_time_ms: float = 0.0


@dataclass
class LoadSheddingDecision:
    task_id: str
    admitted: bool
    priority: WorkloadPriority
    sojourn_time_ms: float
    reason: str


class AdaptiveLoadShedder:
    """Manages active load shedding based on queue sojourn latency thresholds."""

    DEFAULT_TARGET_SOJOURN_MS = 100.0   # Target maximum queue wait time
    DEFAULT_INTERVAL_MS = 500.0         # CoDel evaluation interval

    def __init__(
        self,
        target_sojourn_ms: float = DEFAULT_TARGET_SOJOURN_MS,
        max_queue_depth: int = 100,
    ) -> None:
        self.target_sojourn_ms = target_sojourn_ms
        self.max_queue_depth = max_queue_depth
        self._queue: list[QueuedTask] = []
        self._shedded_tasks_count = 0
        self._admitted_tasks_count = 0

    def enqueue_task(self, task_id: str, priority: WorkloadPriority, payload: dict[str, Any]) -> None:
        task = QueuedTask(
            task_id=task_id,
            priority=priority,
            enqueued_at=time.time(),
            payload=payload,
        )
        self._queue.append(task)

    def evaluate_admission(self) -> Optional[LoadSheddingDecision]:
        """Examine the head of the queue using CoDel sojourn metrics and decide admission or shedding."""
        if not self._queue:
            return None

        task = self._queue.pop(0)
        now = time.time()
        sojourn_ms = (now - task.enqueued_at) * 1000.0
        task.sojourn_time_ms = sojourn_ms

        # Critical user tasks are never shedded
        if task.priority == WorkloadPriority.CRITICAL_USER:
            self._admitted_tasks_count += 1
            return LoadSheddingDecision(
                task_id=task.task_id,
                admitted=True,
                priority=task.priority,
                sojourn_time_ms=round(sojourn_ms, 2),
                reason="Admitted: Critical user task SLA guaranteed.",
            )

        # If queue depth is saturated or sojourn exceeds target, shed low priority tasks
        queue_bloat = len(self._queue) > self.max_queue_depth * 0.7
        sojourn_breached = sojourn_ms > self.target_sojourn_ms

        if (queue_bloat or sojourn_breached) and task.priority in [WorkloadPriority.BACKGROUND, WorkloadPriority.SPECULATIVE]:
            self._shedded_tasks_count += 1
            return LoadSheddingDecision(
                task_id=task.task_id,
                admitted=False,
                priority=task.priority,
                sojourn_time_ms=round(sojourn_ms, 2),
                reason=f"Shedded: CoDel queue threshold breached (sojourn={sojourn_ms:.1f}ms > {self.target_sojourn_ms}ms).",
            )

        self._admitted_tasks_count += 1
        return LoadSheddingDecision(
            task_id=task.task_id,
            admitted=True,
            priority=task.priority,
            sojourn_time_ms=round(sojourn_ms, 2),
            reason="Admitted: Within safe queue bounds.",
        )

    def get_stats(self) -> dict[str, int]:
        return {
            "current_queue_depth": len(self._queue),
            "admitted_tasks": self._admitted_tasks_count,
            "shedded_tasks": self._shedded_tasks_count,
        }
