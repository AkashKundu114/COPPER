"""Unified FinOps Resource Governor & Load Shedding Controller for C.O.P.P.E.R.

Integrates budget tracking, storage quotas, pre-flight admission, and graceful workload
shedding under hardware memory/VRAM constraints.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.core.finops.admission_controller import (
    AdmissionVerdict,
    ResourceAdmissionController,
    resource_admission_controller,
)
from app.core.finops.budgets import (
    AgentResourceBudget,
    ResourceBudgetRegistry,
    resource_budget_registry,
)
from app.core.finops.storage_sentinel import StorageQuotaSentinel, storage_quota_sentinel
from app.core.logger import logger


@dataclass
class WorkloadAdmissionResult:
    allowed: bool
    status: str
    rejection_reason: str | None = None
    shed_load: bool = False
    vram_eviction_suggested: bool = False
    allocated_budget: AgentResourceBudget | None = None


class FinOpsResourceGovernor:
    """Supervises hardware consumption, quota adherence, and workload admission."""

    def __init__(
        self,
        budgets: ResourceBudgetRegistry = resource_budget_registry,
        admission: ResourceAdmissionController = resource_admission_controller,
        storage: StorageQuotaSentinel = storage_quota_sentinel,
    ):
        self.budgets = budgets
        self.admission = admission
        self.storage = storage

    async def admit_workload(
        self,
        task_id: str,
        agent_id: str,
        estimated_vram_gb: float,
        estimated_tokens: int,
        priority: int = 2,
    ) -> WorkloadAdmissionResult:
        """Evaluates system quotas and admits or sheds incoming workload."""
        # 1. Enforce physical storage write admission
        can_write, storage_err = self.storage.can_write_artifact(artifact_size_mb=1.0)
        if not can_write:
            logger.error("[ResourceGovernor] Storage quota CRITICAL (>95%). Shedding workload write.")
            return WorkloadAdmissionResult(
                allowed=False,
                status="STORAGE_QUOTA_EXCEEDED",
                rejection_reason=storage_err or "Storage quota critical (>95% saturation). Halting incoming writes.",
                shed_load=True,
            )

        # 2. Strict 8.0 GB Hardware VRAM Boundary Check
        if estimated_vram_gb > 8.0:
            logger.error(f"[ResourceGovernor] Rejected task '{task_id}': VRAM {estimated_vram_gb}GB > 8.0GB limit.")
            return WorkloadAdmissionResult(
                allowed=False,
                status="VRAM_LIMIT_EXCEEDED",
                rejection_reason=f"Model VRAM requirement ({estimated_vram_gb}GB) exceeds strict 8.0GB ceiling.",
            )

        # 3. Check Task / Agent Budgets
        budget_ok, budget_err = self.budgets.check_task_admission(agent_id, estimated_tokens)
        agent_budget = self.budgets.get_agent_budget(agent_id)
        if not budget_ok:
            logger.warning(f"[ResourceGovernor] Budget exhausted for task '{task_id}': {budget_err}")
            return WorkloadAdmissionResult(
                allowed=False,
                status="TOKEN_BUDGET_EXHAUSTED",
                rejection_reason=budget_err,
                allocated_budget=agent_budget,
            )

        # 4. Evaluate Admission Controller
        verdict: AdmissionVerdict = self.admission.evaluate_task_admission(
            task_id=task_id,
            agent_id=agent_id,
            priority=priority,
            estimated_tokens=estimated_tokens,
        )

        if not verdict.admitted:
            return WorkloadAdmissionResult(
                allowed=False,
                status="ADMISSION_REJECTED",
                rejection_reason=verdict.reason,
                vram_eviction_suggested=("VRAM" in verdict.reason),
                allocated_budget=agent_budget,
            )

        # 5. Admitted successfully
        agent_budget.record_tokens(estimated_tokens)
        logger.info(
            f"[ResourceGovernor] Admitted task '{task_id}' (VRAM={estimated_vram_gb}GB, Tokens={estimated_tokens})"
        )

        return WorkloadAdmissionResult(
            allowed=True,
            status="ADMITTED",
            allocated_budget=agent_budget,
        )


resource_governor = FinOpsResourceGovernor()
