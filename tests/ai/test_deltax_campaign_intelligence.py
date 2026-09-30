"""
Unit tests for DeltaX Campaign Intelligence enhancements:
- Creative Fatigue Detection
- Predictive Pacing & Budget Exhaustion Forecaster
- Multi-Touch Attribution Engine (Linear, Time-Decay, Shapley Values)
- Automated Reporting Generator
"""

from datetime import datetime, timedelta, timezone
import pytest

from app.ai.campaign.attribution import ConversionJourney, Touchpoint, mta_engine
from app.ai.campaign.creative_fatigue import CreativeMetricPoint, creative_fatigue_detector
from app.ai.campaign.forecaster import campaign_forecaster
from app.ai.campaign.report_generator import campaign_report_generator


def test_creative_fatigue_detection():
    now = datetime.now(timezone.utc)
    # Series with escalating frequency and steep CTR decay
    history = [
        CreativeMetricPoint(
            creative_id="crt-test-1",
            campaign_id="cmp-perf-01",
            frequency=1.2,
            ctr=0.045,
            cpa=25.0,
            timestamp=now - timedelta(days=5),
        ),
        CreativeMetricPoint(
            creative_id="crt-test-1",
            campaign_id="cmp-perf-01",
            frequency=2.4,
            ctr=0.038,
            cpa=28.0,
            timestamp=now - timedelta(days=3),
        ),
        CreativeMetricPoint(
            creative_id="crt-test-1",
            campaign_id="cmp-perf-01",
            frequency=3.6,  # Above threshold 3.2
            ctr=0.022,  # >50% decay from peak
            cpa=44.0,
            timestamp=now,
        ),
    ]

    report = creative_fatigue_detector.analyze_creative_series("crt-test-1", "cmp-perf-01", history)
    assert report.is_fatigued is True
    assert report.fatigue_level == "exhausted"
    assert report.ctr_decay_percent > 40.0
    assert "PICASSO" in report.recommendation or "rotate" in report.recommendation.lower()


def test_campaign_forecaster_exhaustion():
    # Spends running at $100/hr from 00:00 to 14:00 ($1400 spent).
    # Daily budget is $1500. Remaining budget is $100.
    # At $100/hr, budget will exhaust in 1 hour (around 15:00).
    spends = [100.0] * 14
    forecast = campaign_forecaster.forecast_budget_exhaustion(
        campaign_id="cmp-test-fast",
        daily_budget=1500.0,
        hourly_spends=spends,
        current_hour=14,
    )

    assert forecast.is_at_risk_of_early_exhaustion is True
    assert forecast.projected_exhaustion_time is not None
    assert "15:00" in forecast.projected_exhaustion_time
    assert len(forecast.projected_values) > 0


def test_multi_touch_attribution_shapley_efficiency_axiom():
    """
    Shapley efficiency axiom: The sum of attributed values to all channels
    must equal the total conversion value across all journeys.
    """
    now = datetime.now(timezone.utc)
    journeys = [
        ConversionJourney(
            journey_id="j1",
            touchpoints=[
                Touchpoint(channel="search", campaign_id="c1", timestamp=now - timedelta(days=2)),
                Touchpoint(channel="social", campaign_id="c2", timestamp=now - timedelta(days=1)),
            ],
            conversion_value=100.0,
            converted_at=now,
        ),
        ConversionJourney(
            journey_id="j2",
            touchpoints=[
                Touchpoint(channel="display", campaign_id="c3", timestamp=now - timedelta(days=3)),
                Touchpoint(channel="search", campaign_id="c1", timestamp=now - timedelta(days=1)),
            ],
            conversion_value=60.0,
            converted_at=now,
        ),
    ]

    total_value = sum(j.conversion_value for j in journeys)
    linear_credits = mta_engine.linear_attribution(journeys)
    shapley_credits = mta_engine.shapley_value_attribution(journeys)

    assert pytest.approx(sum(linear_credits.values()), 0.1) == total_value
    assert pytest.approx(sum(shapley_credits.values()), 0.1) == total_value
    assert "search" in shapley_credits
    assert "social" in shapley_credits


def test_campaign_report_generator_markdown():
    summary = {
        "total_spend": 12450.0,
        "total_conversions": 340,
        "overall_roas": 3.45,
        "avg_ctr": 0.038,
        "avg_cpc": 1.75,
    }
    anomalies = [
        {
            "campaign_name": "Search Performance",
            "metric_name": "CPC",
            "severity": "critical",
            "deviation_percent": 34.5,
            "recommendation": "Adjust bid pacing.",
        }
    ]

    md = campaign_report_generator.generate_markdown_briefing(summary, anomalies)
    assert "# C.O.P.P.E.R. Campaign Intelligence Executive Briefing" in md
    assert "Search Performance" in md
    assert "ROAS" in md
    assert "$12,450.00" in md
