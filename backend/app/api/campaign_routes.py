import asyncio
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.ai.budget_optimizer import budget_optimizer
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
