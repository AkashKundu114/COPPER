"""GPU Energy and Wattage Consumption FinOps Profiler.

Implements Stage 8 Cost & Resource Governance Architecture:
- Tracks and models GPU/CPU dynamic power consumption (Watts, Joules).
- Calculates energy efficiency metrics (Joules per 1K tokens generated, kWh consumed).
- Projects electricity operating costs and flags power/thermal stress limits.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EnergyConsumptionProfile:
    batch_id: str
    tokens_generated: int
    duration_seconds: float
    average_power_watts: float
    total_energy_joules: float
    joules_per_1k_tokens: float
    kwh_consumed: float
    estimated_energy_cost_usd: float
    exceeds_power_cap: bool


class EnergyFinOpsProfiler:
    """Calculates thermodynamic power draw and electrical expenditure for AI inference."""

    # Baseline TDP values (Watts)
    DEFAULT_BASE_IDLE_WATTS = 25.0
    DEFAULT_MAX_TDP_WATTS = 175.0  # Common for mid-tier local GPUs (e.g. RTX 3070/4060)
    DEFAULT_KWH_PRICE_USD = 0.15   # $0.15 per kWh

    def __init__(
        self,
        idle_power_watts: float = DEFAULT_BASE_IDLE_WATTS,
        max_tdp_watts: float = DEFAULT_MAX_TDP_WATTS,
        kwh_price_usd: float = DEFAULT_KWH_PRICE_USD,
        power_budget_cap_watts: float = 160.0,
    ) -> None:
        self.idle_power_watts = idle_power_watts
        self.max_tdp_watts = max_tdp_watts
        self.kwh_price_usd = kwh_price_usd
        self.power_budget_cap_watts = power_budget_cap_watts
        self._batch_history: list[EnergyConsumptionProfile] = []

    def profile_inference_workload(
        self,
        batch_id: str,
        tokens_generated: int,
        duration_seconds: float,
        gpu_utilization_ratio: float = 0.85,
    ) -> EnergyConsumptionProfile:
        """Calculate power and electrical expenditure for an executed inference batch."""
        safe_duration = max(0.001, duration_seconds)
        safe_util = min(1.0, max(0.0, gpu_utilization_ratio))

        # Power (Watts) = Idle + (Max TDP - Idle) * Utilization
        dynamic_power = (self.max_tdp_watts - self.idle_power_watts) * safe_util
        avg_power_watts = self.idle_power_watts + dynamic_power

        # Total Joules = Watts * seconds
        total_joules = avg_power_watts * safe_duration

        # kWh = (Watts * seconds) / (3600 * 1000)
        kwh = (avg_power_watts * safe_duration) / 3_600_000.0

        # Cost = kWh * $/kWh
        cost_usd = kwh * self.kwh_price_usd

        # Joules per 1k tokens
        joules_per_1k = (total_joules / max(1, tokens_generated)) * 1000.0

        exceeds_cap = avg_power_watts > self.power_budget_cap_watts

        profile = EnergyConsumptionProfile(
            batch_id=batch_id,
            tokens_generated=tokens_generated,
            duration_seconds=safe_duration,
            average_power_watts=round(avg_power_watts, 2),
            total_energy_joules=round(total_joules, 2),
            joules_per_1k_tokens=round(joules_per_1k, 2),
            kwh_consumed=kwh,
            estimated_energy_cost_usd=round(cost_usd, 6),
            exceeds_power_cap=exceeds_cap,
        )
        self._batch_history.append(profile)
        return profile

    def get_aggregate_energy_stats(self) -> dict[str, float]:
        """Aggregate total energy and expenditure across all recorded inference workloads."""
        total_kwh = sum(p.kwh_consumed for p in self._batch_history)
        total_cost = sum(p.estimated_energy_cost_usd for p in self._batch_history)
        total_tokens = sum(p.tokens_generated for p in self._batch_history)
        total_joules = sum(p.total_energy_joules for p in self._batch_history)

        avg_joules_1k = (total_joules / max(1, total_tokens)) * 1000.0 if total_tokens > 0 else 0.0

        return {
            "total_workloads_profiled": len(self._batch_history),
            "total_tokens_generated": total_tokens,
            "total_energy_joules": round(total_joules, 2),
            "total_kwh_consumed": round(total_kwh, 6),
            "total_electricity_cost_usd": round(total_cost, 6),
            "avg_joules_per_1k_tokens": round(avg_joules_1k, 2),
        }
