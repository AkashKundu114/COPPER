"""Workload Admission Controller & Graceful Workload Shedder for C.O.P.P.E.R.

Prevents task queue collapse, VRAM thrashing, and token budget exhaustion by
evaluating system saturation and agent quotas prior to task execution.
"""

from __future__ import annotations

from typing import Any

from app.core.finops.budgets import resource_budget_registry
from app.core.logger import logger
from app.core.metrics import metrics_registry


class AdmissionVerdict:
    def __init__(self, admitted: bool, reason: str, priority_adjusted: bool = False):
        self.admitted = admitted
        self.reason = reason
        self.priority_adjusted = priority_adjusted


class ResourceAdmissionController:
    """Evaluates proposed workloads against budget availability and host saturation."""

    def __init__(
        self,
        budget_registry: Any | None = None,
        vram_shedding_threshold_pct: float = 85.0,
    ):
        self.budget_registry = budget_registry or resource_budget_registry
        self.vram_threshold_pct = vram_shedding_threshold_pct

    def evaluate_task_admission(
        self,
        task_id: str,
        agent_id: str,
        priority: int,  # 0=CRITICAL, 1=HIGH, 2=NORMAL, 3=BACKGROUND
        estimated_tokens: int = 500,
    ) -> AdmissionVerdict:
        """Determines whether a task should be admitted, shed, or delayed."""
        # 1. Check Agent Token Budget
        allowed, budget_err = self.budget_registry.check_task_admission(agent_id, estimated_tokens)
        if not allowed:
            return AdmissionVerdict(
                admitted=False,
                reason=f"Rejected: {budget_err}",
            )

        # 2. Check Host VRAM & RAM Saturation
        try:
            vram_used = metrics_registry.vram_used_bytes.get()
            vram_total = metrics_registry.vram_total_bytes.get()
            if vram_total > 0:
                vram_pct = (vram_used / vram_total) * 100.0
                if vram_pct >= self.vram_threshold_pct:
                    # Shed non-critical background workloads
                    if priority >= 3:  # BACKGROUND
                        logger.warning(
                            f"[AdmissionController] Shedding BACKGROUND task {task_id}: "
                            f"Host VRAM saturation is {vram_pct:.1f}% (Threshold: {self.vram_threshold_pct}%)."
                        )
                        return AdmissionVerdict(
                            admitted=False,
                            reason=f"Shed due to elevated VRAM pressure ({vram_pct:.1f}% >= {self.vram_threshold_pct}%).",
                        )
        except Exception as e:
            logger.debug(f"[AdmissionController] Hardware metric sampling error: {e}")

        return AdmissionVerdict(
            admitted=True,
            reason="Task admitted within budget and resource headroom.",
        )


resource_admission_controller = ResourceAdmissionController()
