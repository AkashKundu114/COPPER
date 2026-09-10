from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.core.telemetry import format_grafana_tempo_url, get_recent_traces, get_trace_by_id

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
    """
    Returns recent OpenTelemetry distributed traces with full span hierarchy:
    WebSocket -> Router -> Guardian -> Agent -> LLM -> Response.
    """
    traces = get_recent_traces(limit=limit)
    return {
        "traces": traces,
        "total": len(traces),
        "grafana_base_url": settings.GRAFANA_URL,
    }


@router.get("/traces/{trace_id}")
async def get_distributed_trace(trace_id: str):
    """
    Returns detailed OpenTelemetry trace by trace_id including all child spans,
    attributes, start/end timestamps, and deep-link to Grafana Tempo.
    """
    trace = get_trace_by_id(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    return trace
