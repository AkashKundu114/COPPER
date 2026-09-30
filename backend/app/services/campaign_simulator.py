from datetime import UTC, datetime, timedelta
import math
import random
from typing import Any

from sqlalchemy.orm import Session

from app.database.models.campaign import CampaignMetric
from app.database.postgres import SessionLocal

# Default 5 realistic advertising campaigns representing Brand, Performance, and Retargeting
DEFAULT_CAMPAIGNS: list[dict[str, Any]] = [
    {
        "campaign_id": "cmp-brand-01",
        "campaign_name": "Brand Awareness - Global Reach",
        "campaign_type": "brand",
        "daily_budget": 1500.0,
        "base_impressions": 25000,
        "base_ctr": 0.016,  # 1.6%
        "base_cpc": 0.85,  # $0.85
        "base_cvr": 0.02,  # 2.0%
        "avg_order_value": 55.0,  # $55
    },
    {
        "campaign_id": "cmp-perf-01",
        "campaign_name": "Search Performance - High Intent",
        "campaign_type": "performance",
        "daily_budget": 2800.0,
        "base_impressions": 14000,
        "base_ctr": 0.038,  # 3.8%
        "base_cpc": 2.45,  # $2.45
        "base_cvr": 0.052,  # 5.2%
        "avg_order_value": 95.0,  # $95
    },
    {
        "campaign_id": "cmp-perf-02",
        "campaign_name": "Social Performance - Lookalikes",
        "campaign_type": "performance",
        "daily_budget": 2200.0,
        "base_impressions": 18000,
        "base_ctr": 0.029,  # 2.9%
        "base_cpc": 1.90,  # $1.90
        "base_cvr": 0.041,  # 4.1%
        "avg_order_value": 85.0,  # $85
    },
    {
        "campaign_id": "cmp-retarget-01",
        "campaign_name": "Cart Abandoners - Dynamic Retargeting",
        "campaign_type": "retargeting",
        "daily_budget": 900.0,
        "base_impressions": 4500,
        "base_ctr": 0.068,  # 6.8%
        "base_cpc": 1.65,  # $1.65
        "base_cvr": 0.095,  # 9.5%
        "avg_order_value": 115.0,  # $115
    },
    {
        "campaign_id": "cmp-retarget-02",
        "campaign_name": "VIP Customers - Loyalty Retention",
        "campaign_type": "retargeting",
        "daily_budget": 700.0,
        "base_impressions": 3200,
        "base_ctr": 0.058,  # 5.8%
        "base_cpc": 1.45,  # $1.45
        "base_cvr": 0.088,  # 8.8%
        "avg_order_value": 135.0,  # $135
    },
]


def _get_hourly_diurnal_multiplier(hour: int) -> float:
    """Simulates natural intraday e-commerce traffic fluctuations."""
    # Peak traffic around 14:00 - 21:00, trough around 02:00 - 05:00
    angle = (hour - 3) * (2 * math.pi / 24)
    # Oscillates between ~0.55 (night) and ~1.45 (prime time)
    return max(0.45, 1.0 + 0.45 * math.sin(angle))


def generate_hourly_metric(
    campaign_config: dict[str, Any],
    timestamp: datetime,
    anomaly_type: str | None = None,
    anomaly_intensity: float = 1.0,
) -> CampaignMetric:
    """
    Generates a single hourly synthetic campaign record.
    Supports injecting anomalies:
      - 'ctr_drop': Sudden CTR collapse (ad fatigue/audience saturation)
      - 'budget_spike' / 'cpc_spike': Rapid CPC inflation from competitor bidding
      - 'conversion_drop': Broken checkout/landing page collapse
      - 'impression_drop': Targeting error or platform budget stall
      - 'budget_burn': Extreme spend burning through daily budget
    """
    hour = timestamp.hour
    diurnal = _get_hourly_diurnal_multiplier(hour)

    base_imp = campaign_config["base_impressions"]
    base_ctr = campaign_config["base_ctr"]
    base_cpc = campaign_config["base_cpc"]
    base_cvr = campaign_config["base_cvr"]
    aov = campaign_config["avg_order_value"]
    daily_budget = float(campaign_config["daily_budget"])

    # Normal stochastic noise (+/- 8% variance)
    imp_noise = random.uniform(0.92, 1.08)
    ctr_noise = random.uniform(0.94, 1.06)
    cpc_noise = random.uniform(0.95, 1.05)
    cvr_noise = random.uniform(0.93, 1.07)

    impressions = int(base_imp * diurnal * imp_noise)
    ctr = max(0.001, base_ctr * ctr_noise)
    cpc = max(0.10, base_cpc * cpc_noise)
    cvr = max(0.001, base_cvr * cvr_noise)

    # Apply Anomaly Injections
    if anomaly_type in ("ctr_drop", "sudden_ctr_drop"):
        ctr *= max(0.15, 0.30 / anomaly_intensity)
    elif anomaly_type in ("cpc_spike", "budget_spike"):
        cpc *= (2.4 * anomaly_intensity)
    elif anomaly_type in ("conversion_drop", "conversion_collapse"):
        cvr *= max(0.08, 0.18 / anomaly_intensity)
    elif anomaly_type in ("impression_drop", "reach_collapse"):
        impressions = max(50, int(impressions * max(0.1, 0.25 / anomaly_intensity)))
    elif anomaly_type in ("budget_burn", "burn_rate_spike"):
        cpc *= (2.2 * anomaly_intensity)
        ctr *= 1.3
        impressions = int(impressions * 1.4)

    # Derived metrics
    clicks = max(1, int(round(impressions * ctr)))
    conversions = int(round(clicks * cvr))
    spend = round(clicks * cpc, 2)
    revenue = round(conversions * aov, 2)
    actual_ctr = round(clicks / max(1, impressions), 4)
    actual_cpc = round(spend / max(1, clicks), 2)
    actual_cpa = round(spend / max(1, conversions), 2) if conversions > 0 else spend
    roas = round(revenue / max(0.01, spend), 2)
    budget_utilization = round(spend / max(1.0, daily_budget), 4)

    return CampaignMetric(
        campaign_id=campaign_config["campaign_id"],
        campaign_name=campaign_config["campaign_name"],
        campaign_type=campaign_config["campaign_type"],
        timestamp=timestamp,
        impressions=impressions,
        clicks=clicks,
        conversions=conversions,
        spend=spend,
        revenue=revenue,
        ctr=actual_ctr,
        cpc=actual_cpc,
        cpa=actual_cpa,
        roas=roas,
        daily_budget=daily_budget,
        budget_utilization=budget_utilization,
    )


def generate_campaign_history(
    days: int = 30,
    db: Session | None = None,
    campaigns: list[dict[str, Any]] | None = None,
) -> list[CampaignMetric]:
    """
    Populates the database with `days` (default 30) of hourly synthetic metrics
    for 5 ad campaigns, embedding 2-3 naturally occurring anomalies.
    """
    selected_campaigns = campaigns or DEFAULT_CAMPAIGNS
    total_hours = days * 24
    end_time = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=total_hours - 1)

    all_metrics: list[CampaignMetric] = []

    # Define 3 naturally occurring anomalies across the 30-day timeline:
    # 1. cmp-brand-01 experienced sudden CTR drop (ad fatigue) 8-9 days ago
    # 2. cmp-perf-01 experienced a CPC spike (competitor bid war) 4-5 days ago
    # 3. cmp-perf-02 experienced a conversion rate drop (landing page checkout broken) in the past 16 hours
    anom_window_brand = (total_hours - (9 * 24), total_hours - (8 * 24))
    anom_window_cpc = (total_hours - (5 * 24), total_hours - (4 * 24))
    anom_window_cvr = (total_hours - 16, total_hours)

    for h_idx in range(total_hours):
        current_ts = start_time + timedelta(hours=h_idx)
        for cmp in selected_campaigns:
            cid = cmp["campaign_id"]
            anomaly: str | None = None

            if cid == "cmp-brand-01" and anom_window_brand[0] <= h_idx <= anom_window_brand[1]:
                anomaly = "ctr_drop"
            elif cid == "cmp-perf-01" and anom_window_cpc[0] <= h_idx <= anom_window_cpc[1]:
                anomaly = "cpc_spike"
            elif cid == "cmp-perf-02" and anom_window_cvr[0] <= h_idx <= anom_window_cvr[1]:
                anomaly = "conversion_drop"

            metric = generate_hourly_metric(cmp, current_ts, anomaly_type=anomaly)
            all_metrics.append(metric)

    if db is not None:
        try:
            # Clear existing simulated campaign metrics to keep data clean and idempotent
            db.query(CampaignMetric).delete()
            db.bulk_save_objects(all_metrics)
            db.commit()
        except Exception:
            db.rollback()
            raise

    return all_metrics


def ensure_simulated_campaign_data(db: Session | None = None) -> int:
    """Ensures at least 7 days of campaign metrics exist in the DB."""
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        count = db.query(CampaignMetric).count()
        if count < 100:
            metrics = generate_campaign_history(days=30, db=db)
            return len(metrics)
        return count
    finally:
        if should_close:
            db.close()
