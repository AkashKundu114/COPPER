import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_system_vram_status():
    res = client.get("/api/v1/system/models/vram")
    assert res.status_code == 200
    data = res.json()
    assert "always_on_mini_model" in data
    assert "loaded_models" in data
    assert "vram_policy" in data


def test_post_system_keep_mini():
    res = client.post("/api/v1/system/models/keep-mini")
    assert res.status_code == 200
    data = res.json()
    assert data.get("vram_policy_enforced") is True
