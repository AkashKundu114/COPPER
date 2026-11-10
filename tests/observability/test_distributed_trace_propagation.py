import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.telemetry import (
    init_telemetry,
    start_request_trace,
    trace_span,
    get_recent_traces,
    get_trace_by_id,
    live_span_collector,
)


@pytest.fixture(scope="module", autouse=True)
def setup_otel():
    init_telemetry()


@pytest.fixture
def client():
    return TestClient(app)


def test_end_to_end_trace_hierarchy():
    """Verify trace propagation across full request lifecycle:
    User Request -> Context -> Memory -> Reasoning -> Router -> Agent -> Tool -> Execution -> Response
    """
    root_span, trace_id, root_span_id = start_request_trace(
        "copper.chat.pipeline",
        session_id="trace-test-session",
        attributes={"user.request": "Research quantum error correction"},
    )

    with trace_span("copper.context.construction", attributes={"context.tokens": 350}):
        pass

    with trace_span("copper.memory.retrieval", attributes={"memory.query": "quantum error correction", "memory.hits": 4}) as m_span:
        m_span.set_attribute("memory.latency_ms", 12.4)

    with trace_span("copper.reasoning", attributes={"reasoning.strategy": "cot"}):
        with trace_span("copper.router", attributes={"router.selected_agent": "research", "router.confidence": 0.95}):
            pass

    with trace_span("copper.agent.research", attributes={"agent.id": "agent-res-1"}):
        with trace_span("copper.tool.execution", attributes={"tool.name": "web_search"}) as t_span:
            t_span.set_attribute("tool.status", "success")
            t_span.set_attribute("tool.duration_ms", 450.0)

    with trace_span("copper.response.generation", attributes={"response.status": "completed"}):
        pass

    root_span.end()

    # Query LiveSpanCollector
    trace_record = get_trace_by_id(trace_id)
    assert trace_record is not None
    assert trace_record["trace_id"] == trace_id
    assert len(trace_record["spans"]) >= 7

    span_names = [s["name"] for s in trace_record["spans"]]
    assert "copper.context.construction" in span_names
    assert "copper.memory.retrieval" in span_names
    assert "copper.reasoning" in span_names
    assert "copper.router" in span_names
    assert "copper.agent.research" in span_names
    assert "copper.tool.execution" in span_names
    assert "copper.response.generation" in span_names


def test_api_telemetry_traces_endpoints(client):
    """Verify HTTP API endpoints for retrieving traces."""
    span, trace_id, _ = start_request_trace("copper.api.test_trace", session_id="api-test")
    span.end()

    response = client.get("/api/v1/telemetry/traces?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "traces" in data
    assert "total" in data
    assert data["total"] > 0

    trace_resp = client.get(f"/api/v1/telemetry/traces/{trace_id}")
    assert trace_resp.status_code == 200
    trace_data = trace_resp.json()
    assert trace_data["trace_id"] == trace_id


def test_nonexistent_trace_returns_404(client):
    """Verify requesting invalid trace_id returns 404."""
    response = client.get("/api/v1/telemetry/traces/nonexistent_trace_99999")
    assert response.status_code == 404
