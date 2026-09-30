from datetime import UTC, datetime, timedelta
import json
import pytest
from fastapi.testclient import TestClient

from app.ai.agents.campaign_agent import campaign_agent
from app.ai.budget_optimizer import budget_optimizer, BudgetOptimizer
from app.ai.campaign_anomaly_detector import (
    CampaignAnomalyDetector,
    RECOMMENDATION_TEMPLATES,
    campaign_anomaly_detector,
)
from app.ai.orchestration.agent_router import route_message, route_message_detailed
from app.core.constants import AgentType
from app.database.models.campaign import CampaignMetric
from app.main import app
from app.services.campaign_simulator import (
    DEFAULT_CAMPAIGNS,
    generate_campaign_history,
    generate_hourly_metric,
)


# 1. Test campaign data generation produces valid metrics
def test_campaign_data_generation_valid_metrics():
    now = datetime.now(UTC)
    for cmp_cfg in DEFAULT_CAMPAIGNS:
        metric = generate_hourly_metric(cmp_cfg, now)
        assert metric.campaign_id == cmp_cfg["campaign_id"]
        assert metric.impressions > 0
        assert metric.clicks >= 1
        assert metric.spend > 0.0
        assert 0.001 <= metric.ctr <= 0.20
        assert metric.cpc > 0.0
        assert metric.daily_budget == cmp_cfg["daily_budget"]
        assert metric.budget_utilization > 0.0
        d = metric.to_dict()
        assert "campaign_id" in d
        assert "roas" in d
        assert "cpa" in d


# 2. Test 30-day campaign history generation
def test_campaign_history_generation():
    metrics = generate_campaign_history(days=2, db=None)
    # 2 days * 24 hours * 5 campaigns = 240 records
    assert len(metrics) == 2 * 24 * len(DEFAULT_CAMPAIGNS)
    # Ensure all 5 campaign IDs are present
    cids = {m.campaign_id for m in metrics}
    assert len(cids) == len(DEFAULT_CAMPAIGNS)


# 3. Test Z-score anomaly detection catches injected CTR drop
def test_z_score_anomaly_detection_catches_injected_ctr_drop():
    detector = CampaignAnomalyDetector(z_score_threshold=2.0)
    cmp_cfg = DEFAULT_CAMPAIGNS[0]
    now = datetime.now(UTC)

    # Build 40 hours of normal baseline metrics
    baseline = [
        generate_hourly_metric(cmp_cfg, now - timedelta(hours=40 - i))
        for i in range(40)
    ]

    # Inject sudden CTR collapse on the latest metric
    anomalous = generate_hourly_metric(
        cmp_cfg, now, anomaly_type="ctr_drop", anomaly_intensity=2.0
    )
    all_metrics = baseline + [anomalous]

    anomalies = detector.detect_statistical_anomalies(all_metrics)
    ctr_anoms = [a for a in anomalies if a.anomaly_type == "ctr_drop"]

    assert len(ctr_anoms) >= 1
    anom = ctr_anoms[0]
    assert anom.campaign_id == cmp_cfg["campaign_id"]
    assert anom.current_value < anom.expected_value
    assert anom.deviation_percent < -40.0
    assert "creative" in anom.recommendation.lower()


# 4. Test Z-score anomaly detection does NOT flag normal variance
def test_z_score_anomaly_detection_does_not_flag_normal_variance():
    detector = CampaignAnomalyDetector(z_score_threshold=2.5)
    cmp_cfg = DEFAULT_CAMPAIGNS[1]
    now = datetime.now(UTC)

    # 50 hours of nominal data with normal stochastic noise
    normal_series = [
        generate_hourly_metric(cmp_cfg, now - timedelta(hours=50 - i))
        for i in range(50)
    ]

    anomalies = detector.detect_statistical_anomalies(normal_series)
    # Under regular variance, no critical statistical anomalies should be flagged
    crit_anoms = [a for a in anomalies if a.severity == "critical"]
    assert len(crit_anoms) == 0


# 5. Test Z-score anomaly detection catches CPC spike
def test_z_score_anomaly_detection_catches_cpc_spike():
    detector = CampaignAnomalyDetector(z_score_threshold=2.0)
    cmp_cfg = DEFAULT_CAMPAIGNS[1]
    now = datetime.now(UTC)

    baseline = [
        generate_hourly_metric(cmp_cfg, now - timedelta(hours=35 - i))
        for i in range(35)
    ]
    spike_metric = generate_hourly_metric(
        cmp_cfg, now, anomaly_type="cpc_spike", anomaly_intensity=2.5
    )
    anomalies = detector.detect_statistical_anomalies(baseline + [spike_metric])
    cpc_anoms = [a for a in anomalies if a.anomaly_type == "cpc_spike"]

    assert len(cpc_anoms) >= 1
    assert cpc_anoms[0].current_value > cpc_anoms[0].expected_value
    assert "competitor" in cpc_anoms[0].recommendation.lower()


# 6. Test trend detector catches gradual CTR decay
def test_trend_detector_catches_gradual_ctr_decay():
    detector = CampaignAnomalyDetector(trend_threshold=0.15)
    cmp_cfg = DEFAULT_CAMPAIGNS[0]
    now = datetime.now(UTC)

    metrics: list[CampaignMetric] = []
    # 24 hours of normal performance
    for i in range(24):
        metrics.append(generate_hourly_metric(cmp_cfg, now - timedelta(hours=28 - i)))

    # Last 4 hours suffer gradual performance decay (e.g. ad fatigue)
    for i in range(4):
        decayed = generate_hourly_metric(cmp_cfg, now - timedelta(hours=3 - i))
        decayed.ctr = decayed.ctr * 0.55  # 45% decay below 24h baseline
        decayed.roas = decayed.roas * 0.50
        metrics.append(decayed)

    trend_anoms = detector.detect_trend_anomalies(metrics)
    declining = [a for a in trend_anoms if a.anomaly_type == "declining_trend"]
    assert len(declining) >= 1
    assert declining[0].deviation_percent < -15.0


# 7. Test trend detector catches improving trend
def test_trend_detector_catches_improving_trend():
    detector = CampaignAnomalyDetector(trend_threshold=0.15)
    cmp_cfg = DEFAULT_CAMPAIGNS[2]
    now = datetime.now(UTC)

    metrics = [
        generate_hourly_metric(cmp_cfg, now - timedelta(hours=30 - i))
        for i in range(26)
    ]
    # Surge in recent 3 hours
    for i in range(3):
        surging = generate_hourly_metric(cmp_cfg, now - timedelta(hours=2 - i))
        surging.ctr = surging.ctr * 1.50
        surging.roas = surging.roas * 1.60
        metrics.append(surging)

    trend_anoms = detector.detect_trend_anomalies(metrics)
    improving = [a for a in trend_anoms if a.anomaly_type == "improving_trend"]
    assert len(improving) >= 1
    assert improving[0].deviation_percent > 15.0


# 8. Test budget burn rate projector flags fast burn
def test_budget_burn_rate_projector_flags_fast_burn():
    detector = CampaignAnomalyDetector()
    cmp_cfg = DEFAULT_CAMPAIGNS[1]
    daily_budget = 2400.0  # nominal hourly spend ~$100
    now = datetime.now(UTC)

    # Simulate 6 hours elapsed (00:00 to 06:00), but spending $300/hour
    fast_burn_metrics = []
    for i in range(6):
        m = generate_hourly_metric(cmp_cfg, now - timedelta(hours=5 - i))
        m.spend = 320.0  # At $320/hr, budget exhausts in ~7.5 hours total (by 07:30 AM)
        m.daily_budget = daily_budget
        fast_burn_metrics.append(m)

    anomalies = detector.detect_budget_anomalies(
        fast_burn_metrics, current_hour=5, daily_budget=daily_budget
    )
    burn_anoms = [a for a in anomalies if a.anomaly_type == "budget_burn"]
    assert len(burn_anoms) >= 1
    assert "exhaust" in burn_anoms[0].recommendation.lower()
    assert burn_anoms[0].severity == "critical"


# 9. Test budget underutilization detection
def test_budget_underutilization_detected():
    detector = CampaignAnomalyDetector()
    cmp_cfg = DEFAULT_CAMPAIGNS[0]
    daily_budget = 2000.0
    now = datetime.now(UTC)

    # 19 hours elapsed (hour 18, >70% of day elapsed), but only spent $250 (<30% utilization)
    under_metrics = []
    for i in range(19):
        m = generate_hourly_metric(cmp_cfg, now - timedelta(hours=18 - i))
        m.spend = 12.0
        m.daily_budget = daily_budget
        under_metrics.append(m)

    anomalies = detector.detect_budget_anomalies(
        under_metrics, current_hour=18, daily_budget=daily_budget
    )
    under_anoms = [a for a in anomalies if a.anomaly_type == "budget_underutilizing"]
    assert len(under_anoms) >= 1
    assert "expand" in under_anoms[0].recommendation.lower()


# 10. Test response curve fitting on synthetic data
def test_response_curve_fitting_on_synthetic_data():
    spends = [100.0, 250.0, 500.0, 1000.0, 2000.0]
    # Logarithmic synthetic conversions: conversions = 8 * ln(spend) + 12
    conversions = [8.0 * __import__("math").log(s) + 12.0 for s in spends]

    a, b = BudgetOptimizer.fit_response_curve(spends, conversions)
    assert a > 0.0  # Strictly concave diminishing returns
    assert abs(a - 8.0) < 0.5
    assert abs(b - 12.0) < 1.0


# 11. Test budget optimizer produces valid allocation (sum = budget)
def test_budget_optimizer_produces_valid_allocation():
    data = {
        "cmp-1": {
            "campaign_name": "Campaign 1",
            "current_spend": 2000.0,
            "spends": [200, 500, 1000, 1500, 2000],
            "conversions": [15, 30, 48, 62, 70],
        },
        "cmp-2": {
            "campaign_name": "Campaign 2",
            "current_spend": 3000.0,
            "spends": [300, 800, 1500, 2200, 3000],
            "conversions": [10, 22, 35, 44, 50],
        },
        "cmp-3": {
            "campaign_name": "Campaign 3",
            "current_spend": 1000.0,
            "spends": [100, 300, 600, 800, 1000],
            "conversions": [20, 45, 70, 85, 95],
        },
    }

    target_budget = 6000.0
    result = budget_optimizer.optimize_budget(data, total_budget=target_budget)

    # Constraint check: sum of allocations must equal target budget exactly
    total_allocated = sum(result.optimized_allocation.values())
    assert abs(total_allocated - target_budget) < 0.05
    assert len(result.optimized_allocation) == 3
    # Check bounds (all allocations positive)
    for alloc in result.optimized_allocation.values():
        assert alloc > 0


# 12. Test budget optimizer improves projected conversions
def test_budget_optimizer_improves_projected_conversions():
    data = {
        # High elasticity / high yield campaign currently underfunded
        "cmp-high-yield": {
            "campaign_name": "High Yield Retargeting",
            "current_spend": 500.0,
            "spends": [100, 200, 400, 500],
            "conversions": [20, 38, 65, 78],
        },
        # Saturated campaign currently overfunded
        "cmp-saturated": {
            "campaign_name": "Saturated Awareness",
            "current_spend": 3500.0,
            "spends": [1000, 2000, 3000, 3500],
            "conversions": [15, 20, 23, 24],
        },
    }

    result = budget_optimizer.optimize_budget(data, total_budget=4000.0)
    assert result.projected_optimized_conversions >= result.projected_current_conversions
    assert result.improvement_percent >= 0.0
    assert len(result.reasoning) >= 2


# 13. Test campaign agent routes correctly from cascade router
@pytest.mark.asyncio
async def test_campaign_agent_routes_correctly_from_cascade_router():
    queries = [
        "How are my campaigns performing?",
        "Which campaign is underperforming?",
        "Optimize my budget across ad sets",
        "What happened to my CTR yesterday?",
        "Alert me about problems in my advertising campaigns",
        "Show ad ROAS and conversion metrics",
    ]
    for q in queries:
        routed_agent = await route_message(q)
        assert routed_agent == AgentType.CAMPAIGN_INTELLIGENCE

        detailed = await route_message_detailed(q)
        assert detailed.agent == AgentType.CAMPAIGN_INTELLIGENCE
        assert detailed.confidence >= 0.60


# 14. Test campaign agent structured response
@pytest.mark.asyncio
async def test_campaign_agent_structured_response():
    resp_str = await campaign_agent.run("How are my campaigns performing?")
    data = json.loads(resp_str)

    assert "summary" in data
    assert "metrics" in data
    assert "anomalies" in data
    assert "recommendations" in data
    assert "charts_data" in data
    assert len(data["recommendations"]) > 0


# 15. Test recommendation text is populated for each anomaly type
def test_recommendation_text_populated_for_each_anomaly_type():
    expected_types = [
        "ctr_drop",
        "cpc_spike",
        "budget_burn",
        "conversion_drop",
        "roas_decline",
        "budget_underutilizing",
    ]
    for t in expected_types:
        assert t in RECOMMENDATION_TEMPLATES
        rec = campaign_anomaly_detector.get_recommendation(t)
        assert len(rec) > 15


# 16. Test API endpoints return correct data shapes
def test_api_endpoints_return_correct_data_shapes():
    client = TestClient(app)

    # 1. GET /api/campaigns
    res_cmps = client.get("/api/campaigns")
    assert res_cmps.status_code == 200
    cmps = res_cmps.json()
    assert isinstance(cmps, list)
    assert len(cmps) >= 1
    first_cmp_id = cmps[0]["campaign_id"]

    # 2. GET /api/campaigns/{campaign_id}/metrics
    res_metrics = client.get(f"/api/campaigns/{first_cmp_id}/metrics?hours=24")
    assert res_metrics.status_code == 200
    metrics = res_metrics.json()
    assert isinstance(metrics, list)
    assert len(metrics) >= 1

    # 3. GET /api/campaigns/anomalies
    res_anom = client.get("/api/campaigns/anomalies?hours=72")
    assert res_anom.status_code == 200
    assert isinstance(res_anom.json(), list)

    # 4. POST /api/campaigns/optimize-budget
    res_opt = client.post(
        "/api/campaigns/optimize-budget",
        json={"total_budget": 10000.0, "campaign_ids": [c["campaign_id"] for c in cmps]},
    )
    assert res_opt.status_code == 200
    opt_data = res_opt.json()
    assert opt_data["total_budget"] == 10000.0
    assert "optimized_allocation" in opt_data

    # 5. GET /api/campaigns/dashboard
    res_dash = client.get("/api/campaigns/dashboard")
    assert res_dash.status_code == 200
    dash_data = res_dash.json()
    assert "summary" in dash_data
    assert "campaigns" in dash_data
    assert "active_anomalies" in dash_data
    assert "budget_optimization" in dash_data


# 17. Test WebSocket alert streaming delivers anomalies
def test_websocket_alert_streaming_delivers_anomalies():
    client = TestClient(app)
    with client.websocket_connect("/ws/campaign-alerts") as websocket:
        initial = websocket.receive_json()
        assert initial["type"] == "campaign_alerts_snapshot"
        assert "anomalies" in initial
        assert "count" in initial
        # Send client ping
        websocket.send_json({"action": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "pong"
