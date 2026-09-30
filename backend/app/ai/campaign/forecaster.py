"""
Predictive Campaign Pacing & Budget Exhaustion Forecaster.

Modeled on DeltaX Predictive Analytics:
Forecasts intraday and multi-day campaign metrics (spend, conversions, exhaustion timing)
using zero-overhead exponential smoothing to conserve GPU VRAM.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
import numpy as np


@dataclass
class ForecastResult:
    campaign_id: str
    metric_name: str
    historical_mean: float
    projected_values: list[float]
    projected_exhaustion_time: str | None
    is_at_risk_of_early_exhaustion: bool
    confidence_interval: tuple[float, float]
    trend: str  # "accelerating" | "stable" | "decelerating"
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["confidence_interval"] = list(self.confidence_interval)
        return d


class CampaignForecaster:
    """
    Lightweight time-series projection engine for ad-tech metrics.
    """

    @staticmethod
    def exponential_smoothing(series: list[float], alpha: float = 0.35) -> list[float]:
        """Simple exponential smoothing filter for noise reduction."""
        if not series:
            return []
        smoothed = [series[0]]
        for val in series[1:]:
            smoothed.append(alpha * val + (1 - alpha) * smoothed[-1])
        return smoothed

    def forecast_budget_exhaustion(
        self,
        campaign_id: str,
        daily_budget: float,
        hourly_spends: list[float],
        current_hour: int = 14,  # e.g., 2 PM (14:00)
    ) -> ForecastResult:
        if not hourly_spends or daily_budget <= 0:
            return ForecastResult(
                campaign_id=campaign_id,
                metric_name="spend",
                historical_mean=0.0,
                projected_values=[],
                projected_exhaustion_time=None,
                is_at_risk_of_early_exhaustion=False,
                confidence_interval=(0.0, 0.0),
                trend="stable",
                recommendation="No spend history available to forecast.",
            )

        smoothed = self.exponential_smoothing(hourly_spends)
        mean_spend = float(np.mean(smoothed))
        std_spend = float(np.std(smoothed)) if len(smoothed) > 1 else mean_spend * 0.1
        current_cumulative = sum(hourly_spends)

        # Remaining hours in the day
        remaining_hours = max(1, 24 - current_hour)
        projected_spend_per_hour = smoothed[-1]
        projected_total = current_cumulative + (projected_spend_per_hour * remaining_hours)

        # Calculate exhaustion hour if burning too quickly
        exhaustion_time = None
        is_at_risk = False
        remaining_budget = max(0.0, daily_budget - current_cumulative)

        if projected_spend_per_hour > 0 and remaining_budget > 0:
            hours_to_exhaust = remaining_budget / projected_spend_per_hour
            if hours_to_exhaust < remaining_hours:
                is_at_risk = True
                exhaust_hour = int(current_hour + hours_to_exhaust)
                exhaustion_time = f"{exhaust_hour:02d}:00 Today"

        if is_at_risk:
            rec = (
                f"Campaign {campaign_id} will exhaust budget by {exhaustion_time} "
                f"at current velocity. Reduce target CPA/bid by 15% or expand daily budget by "
                f"${projected_total - daily_budget:,.2f}."
            )
        else:
            rec = f"Budget pacing is on schedule to utilize {min(100.0, (projected_total / daily_budget) * 100):.1f}% of daily allocation."

        # Trend detection
        if len(smoothed) >= 3:
            recent_delta = smoothed[-1] - smoothed[-3]
            trend = "accelerating" if recent_delta > 0.05 * mean_spend else "decelerating" if recent_delta < -0.05 * mean_spend else "stable"
        else:
            trend = "stable"

        ci_low = max(0.0, mean_spend - 1.96 * std_spend)
        ci_high = mean_spend + 1.96 * std_spend

        return ForecastResult(
            campaign_id=campaign_id,
            metric_name="spend",
            historical_mean=round(mean_spend, 2),
            projected_values=[round(v, 2) for v in smoothed[-6:]],
            projected_exhaustion_time=exhaustion_time,
            is_at_risk_of_early_exhaustion=is_at_risk,
            confidence_interval=(round(ci_low, 2), round(ci_high, 2)),
            trend=trend,
            recommendation=rec,
        )


campaign_forecaster = CampaignForecaster()
