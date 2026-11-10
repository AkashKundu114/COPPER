"""Predictive Multi-Horizon Capacity and Resource Exhaustion Forecaster.

Implements Stage 12 Unified Observability Architecture:
- Implements Holt-Winters double exponential smoothing for trend and level forecasting.
- Projects future GPU VRAM consumption, SQLite disk growth, and queue backpressure 24-72 hours ahead.
- Generates proactive capacity breach alerts before physical hardware thresholds are violated.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CapacityForecast:
    metric_name: str
    current_value: float
    projected_value_24h: float
    projected_value_72h: float
    capacity_limit: float
    breach_projected: bool
    hours_to_exhaustion: Optional[float]
    recommended_action: str


class PredictiveCapacityForecaster:
    """Predicts long-term hardware capacity exhaustion using trend-adjusted exponential smoothing."""

    def __init__(self, alpha: float = 0.3, beta: float = 0.1) -> None:
        self.alpha = alpha  # Level smoothing factor
        self.beta = beta    # Trend smoothing factor
        self._history: dict[str, list[float]] = {}

    def record_reading(self, metric_name: str, value: float) -> None:
        if metric_name not in self._history:
            self._history[metric_name] = []
        self._history[metric_name].append(value)
        if len(self._history[metric_name]) > 100:
            self._history[metric_name].pop(0)

    def forecast_capacity(
        self,
        metric_name: str,
        capacity_limit: float,
        step_duration_hours: float = 1.0,
    ) -> CapacityForecast:
        """Forecast metric trajectory over 24h and 72h horizons."""
        series = self._history.get(metric_name, [])
        if len(series) < 3:
            curr = series[-1] if series else 0.0
            return CapacityForecast(
                metric_name=metric_name,
                current_value=curr,
                projected_value_24h=curr,
                projected_value_72h=curr,
                capacity_limit=capacity_limit,
                breach_projected=False,
                hours_to_exhaustion=None,
                recommended_action="Collecting baseline series.",
            )

        # Double exponential smoothing (Holt's linear trend)
        level = series[0]
        trend = series[1] - series[0]

        for val in series[1:]:
            last_level = level
            level = self.alpha * val + (1 - self.alpha) * (level + trend)
            trend = self.beta * (level - last_level) + (1 - self.beta) * trend

        # Steps ahead
        h24 = 24.0 / step_duration_hours
        h72 = 72.0 / step_duration_hours

        proj_24 = max(0.0, level + h24 * trend)
        proj_72 = max(0.0, level + h72 * trend)
        curr_val = series[-1]

        breach = proj_24 >= capacity_limit or proj_72 >= capacity_limit

        hours_to_exhaustion = None
        if trend > 1e-6:
            steps_left = (capacity_limit - curr_val) / trend
            if steps_left > 0:
                hours_to_exhaustion = round(steps_left * step_duration_hours, 1)

        action = "Nominal trajectory: No capacity intervention required."
        if breach:
            action = f"PREEMPTIVE CAPACITY WARNING: Resource projected to breach {capacity_limit:.2f} within horizon. Trigger automated compaction."

        return CapacityForecast(
            metric_name=metric_name,
            current_value=round(curr_val, 2),
            projected_value_24h=round(proj_24, 2),
            projected_value_72h=round(proj_72, 2),
            capacity_limit=capacity_limit,
            breach_projected=breach,
            hours_to_exhaustion=hours_to_exhaustion,
            recommended_action=action,
        )
