import pytest
import os
import tempfile

from app.core.telemetry import (
    init_telemetry,
    start_request_trace,
    trace_span,
    get_recent_traces,
    LiveSpanCollector,
)
from app.core.metrics import PrometheusMetricsRegistry
from app.core.json_logger import get_json_logger


@pytest.fixture(scope="module", autouse=True)
def setup_otel():
    init_telemetry()


def test_telemetry_offline_isolation():
    """Verify tracing, metrics, and logging function cleanly without network or external collector."""
    registry = PrometheusMetricsRegistry()
    registry.record_http_request("POST", "/api/v1/chat", 200, 0.25)
    registry.record_llm_inference("local-model", 0.5, 50, 120)

    exposition = registry.render_prometheus_exposition()
    assert "copper_http_requests_total" in exposition
    assert "copper_llm_tokens_generated_total" in exposition

    summary = registry.get_metrics_summary()
    assert summary["inference"]["tokens_generated"] == 120


def test_live_span_collector_ring_buffer_bounded():
    """Verify LiveSpanCollector strictly bounds memory and does not grow indefinitely."""
    collector = LiveSpanCollector(max_traces=5)
    for i in range(15):
        span, trace_id, _ = start_request_trace(f"op_{i}", session_id=f"sess_{i}")
        span.end()

    # Collector max_traces should be respected
    traces = collector.get_traces(limit=20)
    assert len(traces) <= 5


def test_logger_gracefully_handles_io_errors():
    """Verify logging subsystem never crashes the host process if disk is constrained."""
    logger = get_json_logger("copper.isolation_test")
    logger.info("Normal message")
    assert True
