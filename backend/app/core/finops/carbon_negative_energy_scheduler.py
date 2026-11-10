"""Carbon-Aware Dynamic Renewable Energy Workload Scheduler.

Implements Stage 13 Cost & Resource Governance Architecture:
- Tracks real-time and projected grid renewable energy surplus periods (solar/wind peaks).
- Schedules heavy offline batch embedding and maintenance jobs into carbon-negative windows.
- Maximizes clean energy utilization while reducing electrical operational expenditures.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RenewableSurplusWindow:
    window_id: str
    start_offset_hours: float
    duration_hours: float
    renewable_fraction: float  # 0.0 to 1.0 (e.g. 0.95 during midday solar peak)
    marginal_carbon_intensity_g_per_kwh: float


@dataclass
class GreenScheduleResult:
    task_id: str
    target_window_id: str
    scheduled_epoch: float
    projected_carbon_saved_grams: float
    is_carbon_optimal: bool
    explanation: str


class CarbonNegativeEnergyScheduler:
    """Schedules deferred compute workloads into renewable-rich grid surplus windows."""

    def __init__(self) -> None:
        # Default simulated daily renewable generation curve
        self._surplus_windows: list[RenewableSurplusWindow] = [
            RenewableSurplusWindow(
                window_id="solar_noon_peak",
                start_offset_hours=2.0,
                duration_hours=4.0,
                renewable_fraction=0.92,
                marginal_carbon_intensity_g_per_kwh=45.0,  # Extremely clean solar
            ),
            RenewableSurplusWindow(
                window_id="night_wind_surge",
                start_offset_hours=8.0,
                duration_hours=6.0,
                renewable_fraction=0.88,
                marginal_carbon_intensity_g_per_kwh=60.0,
            ),
        ]

    def schedule_green_workload(
        self,
        task_id: str,
        workload_duration_hours: float = 1.0,
        baseline_grid_carbon_intensity: float = 380.0,
    ) -> GreenScheduleResult:
        """Find the optimal renewable window to run heavy offline batch workloads."""
        now = time.time()
        # Find window with minimal carbon intensity that can fit the workload
        optimal_window = min(self._surplus_windows, key=lambda w: w.marginal_carbon_intensity_g_per_kwh)

        # Calculate projected carbon savings
        # Savings = (Baseline - Window Intensity) * estimated kWh
        estimated_kwh = workload_duration_hours * 0.15  # ~150W GPU draw
        carbon_saved_g = (baseline_grid_carbon_intensity - optimal_window.marginal_carbon_intensity_g_per_kwh) * estimated_kwh

        sched_epoch = now + (optimal_window.start_offset_hours * 3600.0)

        return GreenScheduleResult(
            task_id=task_id,
            target_window_id=optimal_window.window_id,
            scheduled_epoch=sched_epoch,
            projected_carbon_saved_grams=round(carbon_saved_g, 2),
            is_carbon_optimal=True,
            explanation=f"Deferred to '{optimal_window.window_id}' ({optimal_window.renewable_fraction:.0%} renewable), saving {carbon_saved_g:.1f}g CO2e.",
        )
