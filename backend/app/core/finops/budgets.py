"""Hierarchical Resource Budget Policy & Registry for C.O.P.P.E.R.

Defines configurable token quotas, dollar spend caps, storage thresholds,
and VRAM saturation limits per agent, task, and billing cycle.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.logger import logger


@dataclass
class AgentResourceBudget:
    agent_id: str
    max_tokens_per_task: int = 4096
    max_tokens_per_hour: int = 50000
    max_execution_time_seconds: float = 60.0
    allow_external_fallback: bool = False
    tokens_consumed_this_hour: int = 0

    def has_available_tokens(self, requested_tokens: int = 1) -> bool:
        return (self.tokens_consumed_this_hour + requested_tokens) <= self.max_tokens_per_hour

    def record_tokens(self, tokens: int) -> None:
        self.tokens_consumed_this_hour += max(0, tokens)

    def reset_hourly_usage(self) -> None:
        self.tokens_consumed_this_hour = 0


@dataclass
class GlobalFinOpsBudget:
    max_monthly_external_spend_usd: float = 10.0
    max_storage_quota_mb: float = 5120.0  # 5 GB
    vram_saturation_threshold_pct: float = 85.0
    current_monthly_spend_usd: float = 0.0
    current_storage_used_mb: float = 250.0

    def can_spend_usd(self, amount: float) -> bool:
        return (self.current_monthly_spend_usd + amount) <= self.max_monthly_external_spend_usd

    def record_spend_usd(self, amount: float) -> None:
        self.current_monthly_spend_usd += max(0.0, amount)


class ResourceBudgetRegistry:
    """Central registry tracking active agent and global FinOps resource budgets."""

    def __init__(self):
        self.global_budget = GlobalFinOpsBudget()
        self._agent_budgets: dict[str, AgentResourceBudget] = {
            "CODING": AgentResourceBudget(agent_id="CODING", max_tokens_per_task=8192, max_tokens_per_hour=100000),
            "RESEARCH": AgentResourceBudget(agent_id="RESEARCH", max_tokens_per_task=8192, max_tokens_per_hour=80000),
            "CHAT": AgentResourceBudget(agent_id="CHAT", max_tokens_per_task=4096, max_tokens_per_hour=30000),
            "DOCUMENT": AgentResourceBudget(agent_id="DOCUMENT", max_tokens_per_task=6144, max_tokens_per_hour=50000),
        }

    def get_agent_budget(self, agent_id: str) -> AgentResourceBudget:
        clean_id = agent_id.upper().strip()
        if clean_id not in self._agent_budgets:
            self._agent_budgets[clean_id] = AgentResourceBudget(agent_id=clean_id)
        return self._agent_budgets[clean_id]

    def check_task_admission(self, agent_id: str, estimated_tokens: int = 500) -> tuple[bool, str | None]:
        b = self.get_agent_budget(agent_id)
        if not b.has_available_tokens(estimated_tokens):
            msg = f"Token budget exceeded for agent '{agent_id}': {b.tokens_consumed_this_hour}/{b.max_tokens_per_hour} tokens consumed this hour."
            logger.warning(f"[FinOps] {msg}")
            return False, msg
        return True, None

    def to_dict(self) -> dict[str, Any]:
        return {
            "global_budget": asdict(self.global_budget),
            "agent_budgets": {k: asdict(v) for k, v in self._agent_budgets.items()},
        }


resource_budget_registry = ResourceBudgetRegistry()
