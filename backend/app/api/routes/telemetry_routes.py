from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List

from app.core.config import settings
from app.core.telemetry import get_recent_traces, get_trace_by_id
from app.core.metrics import metrics_registry
from app.core.alert_sentinel import alert_sentinel

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/status")
async def get_telemetry_status():
    """Returns the OpenTelemetry tracing configuration and health."""
    return {
        "enabled": settings.OTEL_ENABLED,
        "service_name": settings.OTEL_SERVICE_NAME,
        "exporter_endpoint": settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        "grafana_url": settings.GRAFANA_URL,
    }


@router.get("/traces")
async def list_distributed_traces(limit: int = Query(50, ge=1, le=200)):
    """Returns recent OpenTelemetry distributed traces with full span hierarchy."""
    traces = get_recent_traces(limit=limit)
    return {
        "traces": traces,
        "total": len(traces),
        "grafana_base_url": settings.GRAFANA_URL,
    }


@router.get("/traces/{trace_id}")
async def get_distributed_trace(trace_id: str):
    """Returns detailed OpenTelemetry trace by trace_id including all child spans."""
    trace = get_trace_by_id(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    return trace


@router.get("/metrics")
async def get_telemetry_metrics_summary():
    """Returns in-memory snapshot of all metrics across hardware, inference, agents, and security."""
    return metrics_registry.get_metrics_summary()


@router.get("/alerts")
async def get_active_telemetry_alerts():
    """Evaluates and returns any currently firing or active alerts in COPPER."""
    active = alert_sentinel.evaluate_active_alerts()
    return {
        "alerts": [a.to_dict() for a in active],
        "total_active": len(active),
    }
