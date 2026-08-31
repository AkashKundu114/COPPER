import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.wake_word_service import wake_word_service
from app.ai.llm.model_tier_manager import model_tier_manager


@pytest.fixture
def client():
    return TestClient(app)


def test_wake_status_endpoint(client):
    response = client.get("/api/v1/voice/wake/status")
    assert response.status_code == 200
    data = response.json()
    assert "listening" in data
    assert "engine" in data
    assert "tier_manager" in data
    assert "gatekeeper_model" in data["tier_manager"]
    assert data["tier_manager"]["gatekeeper_pinned"] is True


def test_wake_enable_and_disable_endpoints(client):
    enable_res = client.post("/api/v1/voice/wake/enable")
    assert enable_res.status_code == 200
    assert enable_res.json()["listening"] is True

    disable_res = client.post("/api/v1/voice/wake/disable")
    assert disable_res.status_code == 200
    assert disable_res.json()["listening"] is False


def test_model_tier_manager_status():
    status = model_tier_manager.status()
    assert "gatekeeper_model" in status
    assert status["gatekeeper_pinned"] is True
    assert isinstance(status["heavy_models_resident"], list)


def test_wake_word_service_lifecycle():
    assert wake_word_service.status()["listening"] is False
    assert wake_word_service.engine == "whisper_fallback"
