"""Autonomous FinOps Budget Governor & Multi-Tier Load Shedder for C.O.P.P.E.R.

Enforces real-time progressive graceful degradation when approaching resource or VRAM
ceilings: automatically steps down model parameter tiers, enforces strict context compression,
and sheds low-priority background workloads to prevent catastrophic out-of-memory crashes.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Any

from app.core.finops.budgets import ResourceBudgetRegistry, resource_budget_registry
from app.core.finops.resource_governor import FinOpsResourceGovernor, resource_governor
from app.core.logger import logger


class DegradationTier(IntEnum):
    NOMINAL = 0      # Full context, full model tiers admitted
    COMPRESSED = 1   # Enforce aggressive context optimization, defer batch tasks
    DOWNGRADED = 2   # Route all inference to lightweight <= 3B quantized models
    LOAD_SHED = 3    # Reject non-critical tasks; emergency VRAM protection active


@dataclass
class DegradationPolicyStatus:
    policy_id: str
    timestamp: float
    current_tier: DegradationTier
    tier_name: str
    vram_headroom_gb: float
    recommended_model: str
    force_context_compression: bool
    accepting_background_tasks: bool
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AutonomousBudgetEnforcer:
    """Dynamically applies degradation tiers based on active hardware and budget utilization."""

    HARDWARE_VRAM_LIMIT_GB: float = 8.0

    def __init__(self, governor: FinOpsResourceGovernor | None = None):
        self.governor = governor or resource_governor
        self._current_tier: DegradationTier = DegradationTier.NOMINAL

    @property
    def current_tier(self) -> DegradationTier:
        return self._current_tier

    def evaluate_and_adjust_tier(self, current_vram_used_gb: float, hourly_token_spend: int = 0) -> DegradationTier:
        """Determines appropriate degradation tier based on VRAM proximity to the 8.0 GB limit."""
        headroom = self.HARDWARE_VRAM_LIMIT_GB - current_vram_used_gb

        if headroom <= 0.8:  # Less than 800MB headroom left
            self._current_tier = DegradationTier.LOAD_SHED
        elif headroom <= 2.0:  # Less than 2GB headroom left
            self._current_tier = DegradationTier.DOWNGRADED
        elif headroom <= 3.5:  # Less than 3.5GB headroom left
            self._current_tier = DegradationTier.COMPRESSED
        else:
            self._current_tier = DegradationTier.NOMINAL

        logger.info(
            f"[AutonomousBudgetEnforcer] Evaluated tier: {self._current_tier.name} "
            f"(VRAM Headroom: {headroom:.2f}GB / 8.0GB)"
        )
        return self._current_tier

    def admit_workload_under_tier(
        self,
        task_id: str,
        priority: str = "normal",  # "low", "normal", "high", "critical"
        requested_model: str = "deepseek-r1:7b",
    ) -> tuple[bool, str, str]:
        """Evaluates admission and determines model routing under the active degradation tier."""
        if self._current_tier == DegradationTier.LOAD_SHED and priority not in ("critical", "high"):
            return False, requested_model, "Task rejected: System in emergency LOAD_SHED mode."

        if self._current_tier in (DegradationTier.DOWNGRADED, DegradationTier.LOAD_SHED):
            # Route down to lightweight gatekeeper model to preserve 8GB budget
            routed_model = "qwen2.5:1.5b"
            reason = f"Admitted under degradation tier '{self._current_tier.name}': Model downgraded to '{routed_model}'"
            return True, routed_model, reason

        return True, requested_model, f"Admitted normally under tier '{self._current_tier.name}'"

    def get_policy_status(self, current_vram_used_gb: float = 4.2) -> DegradationPolicyStatus:
        """Emits current degradation status and FinOps enforcement parameters."""
        tier = self.evaluate_and_adjust_tier(current_vram_used_gb)
        headroom = round(max(0.0, self.HARDWARE_VRAM_LIMIT_GB - current_vram_used_gb), 2)
        now = time.time()

        recommended = "qwen2.5:1.5b" if tier >= DegradationTier.DOWNGRADED else "deepseek-r1:7b"
        force_comp = tier >= DegradationTier.COMPRESSED
        accept_bg = tier < DegradationTier.LOAD_SHED

        pol_id = f"FINOPS-TIER-{hashlib.sha256(str(now).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{pol_id}:{tier.name}:{headroom}".encode()).hexdigest()

        return DegradationPolicyStatus(
            policy_id=pol_id,
            timestamp=now,
            current_tier=tier,
            tier_name=tier.name,
            vram_headroom_gb=headroom,
            recommended_model=recommended,
            force_context_compression=force_comp,
            accepting_background_tasks=accept_bg,
            signature=sig,
        )


autonomous_budget_enforcer = AutonomousBudgetEnforcer()
