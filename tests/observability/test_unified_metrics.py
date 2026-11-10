import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.metrics import metrics_registry, Counter, Gauge, Histogram


@pytest.fixture
def client():
    return TestClient(app)


def test_metrics_registry_primitives():
    """Verify Counter, Gauge, and Histogram primitives function correctly."""
    counter = Counter("test_counter_total", "Test counter metric")
    counter.inc(5.0, {"status": "success"})
    counter.inc(1.0, {"status": "error"})
    assert counter.get({"status": "success"}) == 5.0
    assert counter.get({"status": "error"}) == 1.0

    gauge = Gauge("test_gauge_val", "Test gauge metric")
    gauge.set(42.5, {"node": "worker-1"})
    assert gauge.get({"node": "worker-1"}) == 42.5
    gauge.inc(2.5, {"node": "worker-1"})
    assert gauge.get({"node": "worker-1"}) == 45.0
    gauge.dec(10.0, {"node": "worker-1"})
    assert gauge.get({"node": "worker-1"}) == 35.0

    hist = Histogram("test_hist_seconds", "Test histogram metric", buckets=[0.1, 0.5, 1.0, 5.0])
    hist.observe(0.05, {"endpoint": "/api"})
    hist.observe(0.4, {"endpoint": "/api"})
    hist.observe(2.0, {"endpoint": "/api"})
    data = hist.get({"endpoint": "/api"})
    assert data["count"] == 3
    assert abs(data["sum"] - 2.45) < 1e-4
    assert data["buckets"][0.1] == 1
    assert data["buckets"][0.5] == 2
    assert data["buckets"][5.0] == 3


def test_prometheus_exposition_endpoint(client):
    """Verify /metrics endpoint serves valid Prometheus exposition text format."""
    metrics_registry.record_http_request("GET", "/api/v1/telemetry/status", 200, 0.015)
    metrics_registry.record_hardware_metrics(
        cpu_ratio=0.35,
        ram_used=4_000_000_000,
        ram_total=16_000_000_000,
        gpu_ratio=0.45,
        vram_used=3_500_000_000,
        vram_total=8_589_934_592,
    )
    metrics_registry.record_agent_execution("planner", "success", 0.32)
    metrics_registry.record_llm_inference("qwen2.5-coder:14b", duration_s=1.2, prompt_tokens=40, completion_tokens=100)

    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text

    assert "# HELP copper_cpu_utilization_ratio" in body
    assert "# TYPE copper_cpu_utilization_ratio gauge" in body
    assert "copper_cpu_utilization_ratio 0.35" in body

    assert "# HELP copper_vram_used_bytes" in body
    assert "copper_vram_used_bytes 3500000000" in body

    assert "copper_agent_executions_total{" in body
    assert "copper_llm_tokens_generated_total{" in body


def test_telemetry_metrics_json_summary_endpoint(client):
    """Verify /api/v1/telemetry/metrics returns comprehensive JSON snapshot."""
    metrics_registry.record_agent_execution("test_agent", "success", 0.1)
    metrics_registry.record_security_event("rate_limit_throttle")

    response = client.get("/api/v1/telemetry/metrics")
    assert response.status_code == 200
    data = response.json()

    assert "hardware" in data
    assert "inference" in data
    assert "agents" in data
    assert "security" in data

    assert data["hardware"]["cpu_utilization_ratio"] is not None
    assert data["hardware"]["vram_used_bytes"] is not None
    assert data["agents"]["total_executions"] >= 1
    assert data["security"]["total_violations"] >= 1
