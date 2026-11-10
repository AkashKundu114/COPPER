import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.alert_sentinel import alert_sentinel, AlertSeverity
from app.core.metrics import metrics_registry


@pytest.fixture
def client():
    return TestClient(app)


def test_alert_sentinel_normal_conditions():
    """Verify AlertSentinel raises no hardware alerts under normal operational metrics."""
    alert_sentinel.reset()
    metrics_registry.record_hardware_metrics(
        cpu_ratio=0.25,
        ram_used=4_000_000_000,
        ram_total=16_000_000_000,
        gpu_ratio=0.30,
        vram_used=4_000_000_000,
        vram_total=8_589_934_592,
    )
    metrics_registry.update_queue_depth(2)
    metrics_registry.record_database_health(True)
    metrics_registry.record_telemetry_health(True)

    active_alerts = alert_sentinel.evaluate_active_alerts(sample_hardware=False)
    hw_alerts = [a for a in active_alerts if a.name in ("GPUVRAMPressure", "HostCPUExhaustion", "HostRAMExhaustion")]
    assert len(hw_alerts) == 0


def test_alert_sentinel_vram_pressure():
    """Verify GPUVRAMPressure fires when VRAM consumption exceeds 90% of 8GB constraint."""
    alert_sentinel.reset()
    metrics_registry.record_hardware_metrics(
        cpu_ratio=0.30,
        ram_used=4_000_000_000,
        ram_total=16_000_000_000,
        gpu_ratio=0.95,
        vram_used=int(8_589_934_592 * 0.96),
        vram_total=8_589_934_592,
    )
    active = alert_sentinel.evaluate_active_alerts(sample_hardware=False)
    vram_alert = next((a for a in active if a.name == "GPUVRAMPressure"), None)
    assert vram_alert is not None
    assert vram_alert.severity == AlertSeverity.CRITICAL
    assert "96.0%" in vram_alert.message


def test_alert_sentinel_queue_saturation():
    """Verify InferenceQueueSaturation fires when queue depth exceeds threshold."""
    alert_sentinel.reset()
    metrics_registry.update_queue_depth(15)

    active = alert_sentinel.evaluate_active_alerts(sample_hardware=False)
    queue_alert = next((a for a in active if a.name == "InferenceQueueSaturation"), None)
    assert queue_alert is not None
    assert queue_alert.severity == AlertSeverity.WARNING
    assert "15" in queue_alert.message


def test_alert_sentinel_database_connectivity_down():
    """Verify DatabaseConnectivityDown fires when database connection status is 0."""
    alert_sentinel.reset()
    metrics_registry.record_database_health(False)

    active = alert_sentinel.evaluate_active_alerts(sample_hardware=False)
    db_alert = next((a for a in active if a.name == "DatabaseConnectivityDown"), None)
    assert db_alert is not None
    assert db_alert.severity == AlertSeverity.CRITICAL

    # Restore health
    metrics_registry.record_database_health(True)
    active_after = alert_sentinel.evaluate_active_alerts(sample_hardware=False)
    db_alert_after = next((a for a in active_after if a.name == "DatabaseConnectivityDown"), None)
    assert db_alert_after is None


def test_telemetry_alerts_endpoint(client):
    """Verify /api/v1/telemetry/alerts endpoint returns active alerts formatted as JSON."""
    alert_sentinel.reset()
    metrics_registry.record_database_health(False)
    response = client.get("/api/v1/telemetry/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert "total_active" in data
    assert any(a["name"] == "DatabaseConnectivityDown" for a in data["alerts"])

    # Clean up state
    metrics_registry.record_database_health(True)
