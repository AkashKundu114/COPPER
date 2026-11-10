from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.models.memory_v2 import UserMemoryV2
from app.database.postgres import get_db


@pytest.fixture
def client():
    return TestClient(app)


def test_privacy_policies_endpoint(client):
    """Verify GET /api/v1/privacy/policies returns all 5 classification policies."""
    response = client.get("/api/v1/privacy/policies")
    assert response.status_code == 200
    data = response.json()
    assert "classifications" in data
    assert "public" in data["classifications"]
    assert "internal" in data["classifications"]
    assert "personal" in data["classifications"]
    assert "sensitive" in data["classifications"]
    assert "restricted" in data["classifications"]


def test_user_consent_endpoints(client):
    """Verify GET and POST /api/v1/privacy/consent endpoints."""
    # 1. GET consent
    get_res = client.get("/api/v1/privacy/consent")
    assert get_res.status_code == 200
    c_data = get_res.json()
    assert "telemetry_collection" in c_data

    # 2. Update consent
    update_res = client.post(
        "/api/v1/privacy/consent",
        json={"telemetry_collection": False, "ambient_memory_recording": True, "cloud_model_fallback": False},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()["consent"]
    assert updated_data["telemetry_collection"] is False


def test_export_user_data_endpoint(client):
    """Verify GET /api/v1/privacy/export returns portable structured JSON with checksum."""
    response = client.get("/api/v1/privacy/export")
    assert response.status_code == 200
    data = response.json()

    assert "export_id" in data
    assert "generated_at" in data
    assert "data" in data
    assert "integrity_checksum" in data
    assert len(data["integrity_checksum"]) == 64


def test_correct_user_data_endpoint_nonexistent(client):
    """Verify POST /api/v1/privacy/correct returns 404 if memory item does not exist."""
    response = client.post(
        "/api/v1/privacy/correct",
        json={"memory_id": 999999, "new_content": "Corrected factual statement", "reason": "user_update"},
    )
    assert response.status_code == 404
