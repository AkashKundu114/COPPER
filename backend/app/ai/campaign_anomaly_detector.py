from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database.models.campaign import CampaignMetric


@dataclass
class CampaignAnomaly:
    campaign_id: str
    campaign_name: str
    anomaly_type: str  # "ctr_drop", "cpc_spike", "budget_burn", "conversion_drop", "roas_decline", etc.
    severity: str  # "info", "warning", "critical"
    metric_name: str
    current_value: float
    expected_value: float
    deviation_percent: float
    detected_at: datetime
    recommendation: str
    auto_fixable: bool

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if isinstance(self.detected_at, datetime):
            d["detected_at"] = self.detected_at.isoformat()
        return d


RECOMMENDATION_TEMPLATES: dict[str, str] = {
    "ctr_drop": "Consider refreshing ad creative or narrowing audience targeting",
    "cpc_spike": "Competitor activity detected. Consider adjusting bid strategy or shifting budget to lower-competition hours",
    "budget_burn": "At current spend rate, budget will exhaust by 2 PM. Reduce bids by 15% or increase daily budget",
    "conversion_drop": "Check landing page load time and form functionality",
    "roas_decline": "Pause low-performing ad sets and reallocate budget to top performers",
    "budget_underutilizing": "Expand keyword targeting or increase maximum bid limits to capture untapped volume",
    "declining_trend": "Performance decay detected across recent hours. Review frequency capping and audience fatigue",
    "improving_trend": "Significant performance momentum detected. Consider scaling budget by 10-20% to capture surge",
}


class CampaignAnomalyDetector:
    """
    DeltaX-style anomaly detection engine for advertising campaigns.
    Implements 3 core detection algorithms:
      1. Statistical Z-Score (Rolling 7-day baseline)
      2. Trend-Based Moving Average Crossover (3h vs 24h)
      3. Budget Burn Rate Projection & Underutilization Analysis
    """

    def __init__(self, z_score_threshold: float = 2.0, trend_threshold: float = 0.15):
        self.z_score_threshold = z_score_threshold
        self.trend_threshold = trend_threshold

    def get_recommendation(self, anomaly_type: str, context: dict[str, Any] | None = None) -> str:
        if anomaly_type in RECOMMENDATION_TEMPLATES:
            rec = RECOMMENDATION_TEMPLATES[anomaly_type]
            if anomaly_type == "budget_burn" and context and "exhaustion_time" in context:
                return f"At current spend rate, budget will exhaust by {context['exhaustion_time']}. Reduce bids by 15% or increase daily budget"
            return rec
        return "Inspect campaign bid settings, targeting parameters, and creative assets."

    def detect_statistical_anomalies(
        self, metrics: list[CampaignMetric], target_metric: CampaignMetric | None = None
    ) -> list[CampaignAnomaly]:
        """
        Z-Score Anomaly Detection:
        Computes rolling 7-day (up to 168 hours) mean and std_dev for:
        CTR, CPC, ROAS, conversions.
        Flags any data point where |value - mean| > 2 * std_dev.
        """
        if not metrics or len(metrics) < 10:
            return []

        # Sort chronologically
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp if m.timestamp else datetime.min)
        current = target_metric or sorted_metrics[-1]
        baseline = sorted_metrics[:-1] if target_metric is None else sorted_metrics

        anomalies: list[CampaignAnomaly] = []
        metric_configs = [
            ("ctr", "ctr_drop", "CTR", lambda cur, exp: cur < exp),
            ("cpc", "cpc_spike", "CPC", lambda cur, exp: cur > exp),
            ("roas", "roas_decline", "ROAS", lambda cur, exp: cur < exp),
            ("conversions", "conversion_drop", "conversions", lambda cur, exp: cur < exp),
        ]

        for attr, anom_type, label, is_negative_direction in metric_configs:
            values = np.array([float(getattr(m, attr, 0.0)) for m in baseline], dtype=float)
            mean = float(np.mean(values))
            std_dev = float(np.std(values))

            if std_dev <= 1e-6:
                continue

            current_val = float(getattr(current, attr, 0.0))
            z_score = abs(current_val - mean) / std_dev

            if z_score > self.z_score_threshold:
                dev_pct = round(((current_val - mean) / max(abs(mean), 1e-6)) * 100, 2)
                severity = "critical" if z_score > 3.0 else "warning"

                # Check if it represents an adverse anomaly or notable deviation
                if is_negative_direction(current_val, mean) or z_score >= 2.5:
                    resolved_type = anom_type if is_negative_direction(current_val, mean) else f"{attr}_spike"
                    rec = self.get_recommendation(resolved_type)
                    auto_fixable = anom_type in ("cpc_spike", "ctr_drop", "roas_decline")

                    anomalies.append(
                        CampaignAnomaly(
                            campaign_id=current.campaign_id,
                            campaign_name=current.campaign_name,
                            anomaly_type=resolved_type,
                            severity=severity,
                            metric_name=label,
                            current_value=round(current_val, 4 if attr == "ctr" else 2),
                            expected_value=round(mean, 4 if attr == "ctr" else 2),
                            deviation_percent=dev_pct,
                            detected_at=current.timestamp or datetime.now(UTC),
                            recommendation=rec,
                            auto_fixable=auto_fixable,
                        )
                    )

        return anomalies

    def detect_trend_anomalies(
        self, metrics: list[CampaignMetric], threshold: float | None = None
    ) -> list[CampaignAnomaly]:
        """
        Moving Average Crossover:
        Short-term (3h) vs Long-term (24h) moving average.
        - short_ma < long_ma * (1 - threshold) -> "declining trend"
        - short_ma > long_ma * (1 + threshold) -> "improving trend"
        Catches gradual decay (e.g. ad fatigue).
        """
        thresh = threshold if threshold is not None else self.trend_threshold
        if not metrics or len(metrics) < 24:
            return []

        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp if m.timestamp else datetime.min)
        latest = sorted_metrics[-1]

        # Analyze trends for primary efficiency metrics (CTR and ROAS)
        anomalies: list[CampaignAnomaly] = []

        for metric_key in ("ctr", "roas", "conversions"):
            vals = [float(getattr(m, metric_key, 0.0)) for m in sorted_metrics]
            short_ma = float(np.mean(vals[-3:]))
            long_ma = float(np.mean(vals[-24:]))

            if long_ma <= 1e-6:
                continue

            ratio = (short_ma - long_ma) / long_ma

            if ratio < -thresh:
                dev_pct = round(ratio * 100, 2)
                anomalies.append(
                    CampaignAnomaly(
                        campaign_id=latest.campaign_id,
                        campaign_name=latest.campaign_name,
                        anomaly_type="declining_trend",
                        severity="warning" if abs(ratio) < 0.35 else "critical",
                        metric_name=metric_key.upper(),
                        current_value=round(short_ma, 4 if metric_key == "ctr" else 2),
                        expected_value=round(long_ma, 4 if metric_key == "ctr" else 2),
                        deviation_percent=dev_pct,
                        detected_at=latest.timestamp or datetime.now(UTC),
                        recommendation="Consider refreshing ad creative or narrowing audience targeting"
                        if metric_key == "ctr"
                        else self.get_recommendation("declining_trend"),
                        auto_fixable=True,
                    )
                )
            elif ratio > thresh:
                dev_pct = round(ratio * 100, 2)
                anomalies.append(
                    CampaignAnomaly(
                        campaign_id=latest.campaign_id,
                        campaign_name=latest.campaign_name,
                        anomaly_type="improving_trend",
                        severity="info",
                        metric_name=metric_key.upper(),
                        current_value=round(short_ma, 4 if metric_key == "ctr" else 2),
                        expected_value=round(long_ma, 4 if metric_key == "ctr" else 2),
                        deviation_percent=dev_pct,
                        detected_at=latest.timestamp or datetime.now(UTC),
                        recommendation=self.get_recommendation("improving_trend"),
                        auto_fixable=False,
                    )
                )

        return anomalies

    def detect_budget_anomalies(
        self,
        metrics: list[CampaignMetric],
        current_hour: int | None = None,
        daily_budget: float | None = None,
    ) -> list[CampaignAnomaly]:
        """
        Burn Rate Projection & Budget Underutilization:
        Given daily_budget and current hourly spend rate:
        - If projected exhaustion time leaves > 40% of the day unspent (i.e. exhaustion happens with
          > 60% of day remaining or hours_to_exhaust < remaining_day * 0.6), flag as 'budget burning too fast'.
        - If budget utilization < 30% with > 70% of day elapsed (hour >= 17), flag as 'budget underutilizing'.
        """
        if not metrics:
            return []

        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp if m.timestamp else datetime.min)
        latest = sorted_metrics[-1]
        hour = current_hour if current_hour is not None else (latest.timestamp.hour if latest.timestamp else 12)
        budget = daily_budget or latest.daily_budget

        if budget <= 0:
            return []

        # Calculate spend so far today (last `hour + 1` hours or current hourly rate)
        recent_window = min(len(sorted_metrics), max(1, hour + 1))
        today_metrics = sorted_metrics[-recent_window:]
        today_spend = sum(float(m.spend) for m in today_metrics)
        avg_hourly_spend = float(np.mean([float(m.spend) for m in today_metrics])) if today_metrics else float(latest.spend)

        utilization_rate = today_spend / budget
        day_elapsed_ratio = (hour + 1) / 24.0
        remaining_hours = max(0.5, 24 - (hour + 1))

        anomalies: list[CampaignAnomaly] = []

        # 1. Check Fast Burn Rate Projection
        if avg_hourly_spend > 0:
            hours_to_exhaust = (budget - today_spend) / avg_hourly_spend
            # If hours to exhaust is significantly less than remaining hours of the day (e.g. < 60% of remaining day)
            # or if exhaustion occurs when > 60% of the day is left
            is_fast_burn = (hours_to_exhaust < remaining_hours * 0.60) or (today_spend >= budget * 0.85 and hour < 14)
            if is_fast_burn and today_spend < budget:
                exhaustion_clock_hour = int(min(23, hour + max(1, round(hours_to_exhaust))))
                ampm = "AM" if exhaustion_clock_hour < 12 else "PM"
                clock_12 = exhaustion_clock_hour % 12
                clock_str = f"{clock_12 or 12} {ampm}"
                rec = f"At current spend rate, budget will exhaust by {clock_str}. Reduce bids by 15% or increase daily budget"

                anomalies.append(
                    CampaignAnomaly(
                        campaign_id=latest.campaign_id,
                        campaign_name=latest.campaign_name,
                        anomaly_type="budget_burn",
                        severity="critical",
                        metric_name="BURN_RATE",
                        current_value=round(avg_hourly_spend, 2),
                        expected_value=round(budget / 24.0, 2),
                        deviation_percent=round(((avg_hourly_spend - (budget / 24.0)) / (budget / 24.0)) * 100, 2),
                        detected_at=latest.timestamp or datetime.now(UTC),
                        recommendation=rec,
                        auto_fixable=True,
                    )
                )

        # 2. Check Budget Underutilization: utilization < 30% with > 70% of day elapsed (hour >= 17)
        if day_elapsed_ratio > 0.70 and utilization_rate < 0.30:
            anomalies.append(
                CampaignAnomaly(
                    campaign_id=latest.campaign_id,
                    campaign_name=latest.campaign_name,
                    anomaly_type="budget_underutilizing",
                    severity="warning",
                    metric_name="BUDGET_UTILIZATION",
                    current_value=round(utilization_rate * 100, 2),
                    expected_value=round(day_elapsed_ratio * 100, 2),
                    deviation_percent=round((utilization_rate - day_elapsed_ratio) * 100, 2),
                    detected_at=latest.timestamp or datetime.now(UTC),
                    recommendation=self.get_recommendation("budget_underutilizing"),
                    auto_fixable=True,
                )
            )

        return anomalies

    def detect_all_anomalies(self, metrics: list[CampaignMetric]) -> list[CampaignAnomaly]:
        """Runs all three detection methods on the provided metrics list."""
        if not metrics:
            return []

        anomalies: list[CampaignAnomaly] = []
        anomalies.extend(self.detect_statistical_anomalies(metrics))
        anomalies.extend(self.detect_trend_anomalies(metrics))
        anomalies.extend(self.detect_budget_anomalies(metrics))
        return anomalies

    def scan_campaign(self, campaign_id: str, db: Session, hours: int = 168) -> list[CampaignAnomaly]:
        """Scans a single campaign from the database over the specified trailing hours."""
        metrics = (
            db.query(CampaignMetric)
            .filter(CampaignMetric.campaign_id == campaign_id)
            .order_by(desc(CampaignMetric.timestamp))
            .limit(hours)
            .all()
        )
        if not metrics:
            return []
        # Return in ascending chronological order for algorithms
        metrics.reverse()
        return self.detect_all_anomalies(metrics)

    def scan_all_campaigns(self, db: Session, hours: int = 168) -> list[CampaignAnomaly]:
        """Scans all unique campaigns in the database and returns all detected anomalies."""
        campaign_ids = [c[0] for c in db.query(CampaignMetric.campaign_id).distinct().all()]
        all_anomalies: list[CampaignAnomaly] = []
        for cid in campaign_ids:
            all_anomalies.extend(self.scan_campaign(cid, db, hours=hours))
        return all_anomalies


campaign_anomaly_detector = CampaignAnomalyDetector()
