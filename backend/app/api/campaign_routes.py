import asyncio
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.ai.budget_optimizer import budget_optimizer
from app.ai.campaign.attribution import ConversionJourney, Touchpoint, mta_engine
from app.ai.campaign.creative_fatigue import CreativeMetricPoint, creative_fatigue_detector
from app.ai.campaign.forecaster import campaign_forecaster
from app.ai.campaign.report_generator import campaign_report_generator
from app.ai.campaign_anomaly_detector import campaign_anomaly_detector
from app.api.websocket.manager import manager
from app.core.logger import logger
from app.database.models.campaign import CampaignMetric
from app.database.postgres import get_db
from app.services.campaign_simulator import ensure_simulated_campaign_data

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
ws_router = APIRouter(tags=["campaign-alerts-ws"])


class OptimizeBudgetRequest(BaseModel):
    total_budget: float = Field(..., gt=0, description="Total portfolio daily budget to allocate")
    campaign_ids: list[str] | None = Field(default=None, description="Optional subset of campaign IDs to optimize")


@router.get("", summary="Get all campaigns with latest metrics")
def get_campaigns(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Returns all monitored ad campaigns with their latest hourly snapshot metrics and health status."""
    ensure_simulated_campaign_data(db)
    distinct_cids = [c[0] for c in db.query(CampaignMetric.campaign_id).distinct().all()]

    campaign_list: list[dict[str, Any]] = []
    anomalies = campaign_anomaly_detector.scan_all_campaigns(db, hours=48)
    anomaly_map = {a.campaign_id: a.severity for a in anomalies}

    for cid in distinct_cids:
        latest = (
            db.query(CampaignMetric)
            .filter(CampaignMetric.campaign_id == cid)
            .order_by(desc(CampaignMetric.timestamp))
            .first()
        )
        if latest:
            data = latest.to_dict()
            # Determine health status based on detected anomalies
            sev = anomaly_map.get(cid, "healthy")
            data["status"] = sev if sev in ("warning", "critical") else "healthy"
            campaign_list.append(data)

    return campaign_list


@router.get("/anomalies", summary="Scan and detect anomalies across all campaigns")
def get_anomalies(hours: int = Query(168, ge=1, le=720), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Runs statistical, trend, and budget anomaly detection engines across all campaigns."""
    ensure_simulated_campaign_data(db)
    anomalies = campaign_anomaly_detector.scan_all_campaigns(db, hours=hours)
    return [a.to_dict() for a in anomalies]


@router.get("/dashboard", summary="Aggregated campaign intelligence dashboard")
def get_dashboard(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Returns aggregated campaign portfolio metrics, health statuses, active alerts, and optimization preview."""
    ensure_simulated_campaign_data(db)
    campaigns = get_campaigns(db)
    anomalies = [a.to_dict() for a in campaign_anomaly_detector.scan_all_campaigns(db, hours=72)]

    total_spend = sum(float(c.get("spend", 0.0)) for c in campaigns) * 24.0
    total_conversions = sum(int(c.get("conversions", 0)) for c in campaigns) * 24
    total_revenue = sum(float(c.get("revenue", 0.0)) for c in campaigns) * 24.0
    overall_roas = round(total_revenue / max(1.0, total_spend), 2) if total_spend > 0 else 0.0

    avg_ctr = (
        round(sum(float(c.get("ctr", 0.0)) for c in campaigns) / len(campaigns), 4)
        if campaigns
        else 0.035
    )
    avg_cpc = (
        round(sum(float(c.get("cpc", 0.0)) for c in campaigns) / len(campaigns), 2)
        if campaigns
        else 1.85
    )

    opt_preview = budget_optimizer.optimize_from_db(db)

    return {
        "summary": {
            "total_spend": round(total_spend, 2),
            "total_conversions": total_conversions,
            "overall_roas": overall_roas,
            "avg_ctr": avg_ctr,
            "avg_cpc": avg_cpc,
            "campaign_count": len(campaigns),
        },
        "campaigns": campaigns,
        "active_anomalies": anomalies,
        "budget_optimization": opt_preview.to_dict(),
    }


@router.post("/optimize-budget", summary="Optimize portfolio budget allocation")
def optimize_budget_endpoint(
    body: OptimizeBudgetRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Computes mathematically optimal budget allocation across campaigns to maximize conversions."""
    ensure_simulated_campaign_data(db)
    opt = budget_optimizer.optimize_from_db(
        db, total_budget=body.total_budget, campaign_ids=body.campaign_ids
    )
    return opt.to_dict()


@router.get("/{campaign_id}/metrics", summary="Get hourly time-series metrics for a campaign")
def get_campaign_metrics(
    campaign_id: str,
    hours: int = Query(168, ge=1, le=720, description="Hours of historical metrics to return"),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Returns time-series hourly performance data for the requested campaign."""
    ensure_simulated_campaign_data(db)
    metrics = (
        db.query(CampaignMetric)
        .filter(CampaignMetric.campaign_id == campaign_id)
        .order_by(desc(CampaignMetric.timestamp))
        .limit(hours)
        .all()
    )
    if not metrics:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")

    metrics.reverse()
    return [m.to_dict() for m in metrics]


@router.get("/creative-fatigue", summary="Detect creative fatigue and audience saturation (DeltaX Engine)")
def get_creative_fatigue(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Evaluates creative fatigue across active ad sets via exposure frequency and CTR decay."""
    ensure_simulated_campaign_data(db)
    distinct_cids = [c[0] for c in db.query(CampaignMetric.campaign_id).distinct().all()]

    reports: list[dict[str, Any]] = []
    now = datetime.now()

    for cid in distinct_cids:
        # Generate representative creative historical data points for each campaign
        pts = [
            CreativeMetricPoint(
                creative_id=f"crt-{cid}-v1",
                campaign_id=cid,
                frequency=1.2 + (i * 0.4),
                ctr=max(0.01, 0.045 - (i * 0.005)),
                cpa=25.0 + (i * 3.5),
                timestamp=now - timedelta(hours=(6 - i) * 12),
            )
            for i in range(6)
        ]
        rep = creative_fatigue_detector.analyze_creative_series(f"crt-{cid}-v1", cid, pts)
        reports.append(rep.to_dict())

    return reports


@router.get("/pacing-forecast", summary="Predictive budget pacing and exhaustion timing (DeltaX Forecaster)")
def get_pacing_forecast(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Projects hour-by-hour campaign spend and predicts budget exhaustion timing."""
    ensure_simulated_campaign_data(db)
    distinct_cids = [c[0] for c in db.query(CampaignMetric.campaign_id).distinct().all()]

    forecasts: list[dict[str, Any]] = []
    for cid in distinct_cids:
        metrics = (
            db.query(CampaignMetric)
            .filter(CampaignMetric.campaign_id == cid)
            .order_by(desc(CampaignMetric.timestamp))
            .limit(24)
            .all()
        )
        if metrics:
            spends = [float(m.spend) for m in reversed(metrics)]
            daily_budget = float(metrics[0].daily_budget) or 1500.0
            fc = campaign_forecaster.forecast_budget_exhaustion(cid, daily_budget, spends)
            forecasts.append(fc.to_dict())

    return forecasts


@router.get("/attribution", summary="Multi-touch cross-channel attribution modeling (DeltaX MTA)")
def get_attribution() -> dict[str, Any]:
    """Computes Linear, Time-Decay, and Game-Theoretic Shapley Value attribution across marketing channels."""
    now = datetime.now()
    # Sample cross-channel conversion journeys
    sample_journeys = [
        ConversionJourney(
            journey_id="j1",
            touchpoints=[
                Touchpoint(channel="search", campaign_id="cmp-perf-01", timestamp=now - timedelta(days=5)),
                Touchpoint(channel="social", campaign_id="cmp-perf-02", timestamp=now - timedelta(days=3)),
                Touchpoint(channel="retargeting", campaign_id="cmp-retarget-01", timestamp=now - timedelta(days=1)),
            ],
            conversion_value=120.0,
            converted_at=now,
        ),
        ConversionJourney(
            journey_id="j2",
            touchpoints=[
                Touchpoint(channel="social", campaign_id="cmp-perf-02", timestamp=now - timedelta(days=2)),
                Touchpoint(channel="search", campaign_id="cmp-perf-01", timestamp=now - timedelta(days=1)),
            ],
            conversion_value=85.0,
            converted_at=now,
        ),
        ConversionJourney(
            journey_id="j3",
            touchpoints=[
                Touchpoint(channel="display", campaign_id="cmp-brand-01", timestamp=now - timedelta(days=7)),
                Touchpoint(channel="retargeting", campaign_id="cmp-retarget-01", timestamp=now - timedelta(hours=6)),
            ],
            conversion_value=150.0,
            converted_at=now,
        ),
    ]

    return {
        "linear": mta_engine.linear_attribution(sample_journeys),
        "time_decay": mta_engine.time_decay_attribution(sample_journeys, half_life_days=3.0),
        "shapley_value": mta_engine.shapley_value_attribution(sample_journeys),
        "total_analyzed_revenue": sum(j.conversion_value for j in sample_journeys),
        "journey_count": len(sample_journeys),
    }


@router.get("/executive-report", summary="Automated campaign briefing document (SCRIBE Bridge)")
def get_executive_report(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Generates an executive briefing document summarizing portfolio health and optimizations."""
    dashboard = get_dashboard(db)
    anomalies = dashboard.get("active_anomalies", [])
    summary = dashboard.get("summary", {})
    optimizations = dashboard.get("budget_optimization")

    md_report = campaign_report_generator.generate_markdown_briefing(
        portfolio_summary=summary,
        anomalies=anomalies,
        optimizations=optimizations,
    )
    return {
        "markdown": md_report,
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
    }


@ws_router.websocket("/ws/campaign-alerts")
async def campaign_alerts_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket endpoint streaming real-time ad-tech anomaly alerts to frontend clients."""
    await manager.connect(websocket)
    try:
        # Send initial active anomalies on connect
        ensure_simulated_campaign_data(db)
        anomalies = campaign_anomaly_detector.scan_all_campaigns(db, hours=72)
        initial_payload = {
            "type": "campaign_alerts_snapshot",
            "count": len(anomalies),
            "anomalies": [a.to_dict() for a in anomalies],
        }
        await websocket.send_json(initial_payload)

        # Listen for client heartbeat or manual refresh triggers
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            if action in ("refresh", "scan"):
                fresh_anomalies = campaign_anomaly_detector.scan_all_campaigns(db, hours=72)
                await websocket.send_json(
                    {
                        "type": "campaign_alerts_snapshot",
                        "count": len(fresh_anomalies),
                        "anomalies": [a.to_dict() for a in fresh_anomalies],
                    }
                )
            elif action == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"Campaign alerts websocket closed: {e}")
        manager.disconnect(websocket)
