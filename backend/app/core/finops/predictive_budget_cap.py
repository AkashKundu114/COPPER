"""Predictive Budget Cap Guard & Autonomous Expenditure Limiter for C.O.P.P.E.R.

Forecasts real-time token expenditure and compute usage against configured hourly and
daily quotas, applying pre-emptive hard caps to prevent runaway token spend or resource exhaustion.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.finops.budgets import ResourceBudgetRegistry, resource_budget_registry
from app.core.logger import logger


@dataclass
class BudgetCapForecastReport:
    report_id: str
    timestamp: float
    hourly_token_limit: int
    hourly_tokens_consumed: int
    hourly_headroom: int
    daily_token_limit: int
    daily_tokens_projected: int
    within_budget_caps: bool
    cap_enforced: bool
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PredictiveBudgetCapGuard:
    """Predictive guard enforcing hard token and resource spend ceilings."""

    DEFAULT_HOURLY_TOKEN_LIMIT: int = 150000
    DEFAULT_DAILY_TOKEN_LIMIT: int = 1000000

    def __init__(
        self,
        budgets: ResourceBudgetRegistry | None = None,
        hourly_limit: int = DEFAULT_HOURLY_TOKEN_LIMIT,
        daily_limit: int = DEFAULT_DAILY_TOKEN_LIMIT,
    ):
        self.budgets = budgets or resource_budget_registry
        self.hourly_limit = hourly_limit
        self.daily_limit = daily_limit
        self._consumed_this_hour: int = 0
        self._last_reset: float = time.time()

    def record_token_consumption(self, tokens: int) -> None:
        """Records consumed tokens and resets hourly window if elapsed."""
        now = time.time()
        if now - self._last_reset >= 3600.0:
            self._consumed_this_hour = 0
            self._last_reset = now
        self._consumed_this_hour += max(0, tokens)

    def evaluate_task_admission(self, estimated_tokens: int) -> tuple[bool, str]:
        """Pre-emptively admits or rejects tasks based on token headroom."""
        self.record_token_consumption(0)  # Check window reset
        projected = self._consumed_this_hour + estimated_tokens

        if projected > self.hourly_limit:
            reason = f"Rejected: Projected hourly tokens ({projected}) would exceed hard limit ({self.hourly_limit})."
            logger.warning(f"[PredictiveBudgetCapGuard] {reason}")
            return False, reason

        return True, "Task admitted within predictive budget cap."

    def generate_forecast_report(self) -> BudgetCapForecastReport:
        """Generates real-time budget forecasting and cap enforcement status report."""
        self.record_token_consumption(0)
        now = time.time()
        headroom = max(0, self.hourly_limit - self._consumed_this_hour)
        projected_daily = self._consumed_this_hour * 24
        within_caps = (self._consumed_this_hour <= self.hourly_limit) and (projected_daily <= self.daily_limit)

        rep_id = f"CAP-{hashlib.sha256(str(now).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{rep_id}:{within_caps}:{headroom}".encode()).hexdigest()

        report = BudgetCapForecastReport(
            report_id=rep_id,
            timestamp=now,
            hourly_token_limit=self.hourly_limit,
            hourly_tokens_consumed=self._consumed_this_hour,
            hourly_headroom=headroom,
            daily_token_limit=self.daily_limit,
            daily_tokens_projected=projected_daily,
            within_budget_caps=within_caps,
            cap_enforced=True,
            signature=sig,
        )

        logger.info(
            f"[PredictiveBudgetCapGuard] Forecast: {self._consumed_this_hour}/{self.hourly_limit} tokens/hr "
            f"(Headroom: {headroom}, WithinCaps: {within_caps})"
        )
        return report


predictive_budget_cap_guard = PredictiveBudgetCapGuard()
