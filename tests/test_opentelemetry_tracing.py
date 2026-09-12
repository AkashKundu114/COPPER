import pytest
from fastapi.testclient import TestClient

from app.core.telemetry import (
    LiveSpanCollector,
    format_grafana_tempo_url,
    get_recent_traces,
    get_trace_by_id,
    init_telemetry,
    live_span_collector,
    start_request_trace,
    trace_span,
)
from app.main import app


def test_telemetry_initialization():
    """Verify OpenTelemetry TracerProvider initializes without error."""
    provider = init_telemetry(app)
    assert provider is not None
    assert live_span_collector is not None


def test_grafana_tempo_url_formatting():
    """Verify deep-link formatting for Grafana Tempo Explore."""
    trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
    url = format_grafana_tempo_url(trace_id)
    assert "explore?left=" in url
    assert "Tempo" in url
    assert trace_id in url


def test_request_lifecycle_tracing():
    """
    Test full request lifecycle tracing:
    WebSocket Request -> Router -> Guardian -> Agent -> LLM -> Response
    """
    session_id = "test-session-123"
    root_span, trace_id, span_id = start_request_trace(
        "copper.websocket.request",
        session_id=session_id,
        attributes={
            "copper.session_id": session_id,
            "copper.message": "Write a python script to test OpenTelemetry",
            "copper.mode": "coding",
            "copper.provider": "ollama",
        },
    )
    assert len(trace_id) == 32
    assert len(span_id) == 16

    # 1. Router Span
    with trace_span("copper.router", attributes={"router.prompt": "Write a python script"}) as r_span:
        r_span.set_attribute("router.selected_agent", "coding")
        r_span.set_attribute("router.confidence", 0.98)
        r_span.set_attribute("router.stage", "fast_pattern_scoring")
        r_span.set_attribute("router.agent_codename", "AXIS")

    # 2. Guardian Span
    with trace_span("copper.guardian", attributes={"guardian.action": "Write a python script"}) as g_span:
        g_span.set_attribute("guardian.verdict_level", "ALLOW")
        g_span.set_attribute("guardian.reasoning", "Safe code generation request")

    # 3. Agent Span
    with trace_span("copper.agent", attributes={"agent.type": "coding", "agent.name": "VULCAN"}) as a_span:
        # 4. LLM Span
        with trace_span("copper.llm", attributes={"llm.model": "qwen2.5-coder-abliterated:14b"}) as l_span:
            l_span.set_attribute("llm.prompt_tokens", 45)
            l_span.set_attribute("llm.completion_tokens", 120)
            l_span.set_attribute("llm.total_tokens", 165)
            l_span.set_attribute("llm.tokens_per_sec", 42.5)
            l_span.set_attribute("llm.latency_ms", 350.2)

    # 5. Response Span
    with trace_span("copper.response", attributes={"response.length": 450, "response.status": "success"}):
        pass

    root_span.end()

    # Query collector
    trace_record = get_trace_by_id(trace_id)
    assert trace_record is not None
    assert trace_record["trace_id"] == trace_id
    assert trace_record["root_name"] == "copper.websocket.request"
    assert trace_record["status"] == "success"
    assert trace_record["spans_count"] >= 6

    span_names = [s["name"] for s in trace_record["spans"]]
    assert "copper.websocket.request" in span_names
    assert "copper.router" in span_names
    assert "copper.guardian" in span_names
    assert "copper.agent" in span_names
    assert "copper.llm" in span_names
    assert "copper.response" in span_names

    # Check child span offsets and durations
    for s in trace_record["spans"]:
        assert "offset_ms" in s
        assert "duration_ms" in s
        assert s["duration_ms"] >= 0


def test_telemetry_api_endpoints():
    """Verify /api/v1/telemetry/traces and /api/v1/telemetry/status HTTP routes."""
    client = TestClient(app)

    # 1. Status endpoint
    resp = client.get("/api/v1/telemetry/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "enabled" in data
    assert data["service_name"] == "copper-backend"
    assert "grafana_url" in data

    # 2. Traces list endpoint
    resp = client.get("/api/v1/telemetry/traces?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "traces" in data
    assert isinstance(data["traces"], list)
    assert "total" in data

    if data["traces"]:
        first_trace = data["traces"][0]
        assert "trace_id" in first_trace
        assert "root_name" in first_trace
        assert "spans" in first_trace

        # 3. Specific trace lookup
        resp = client.get(f"/api/v1/telemetry/traces/{first_trace['trace_id']}")
        assert resp.status_code == 200
        trace_data = resp.json()
        assert trace_data["trace_id"] == first_trace["trace_id"]
