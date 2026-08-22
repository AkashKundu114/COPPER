import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_agents():
    response = client.get("/api/v1/agents/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_agent_versions_not_found():
    response = client.get("/api/v1/agents/nonexistent_agent_xyz/versions")
    assert response.status_code == 200
    assert response.json() == []


def test_agent_disable_nonexistent():
    response = client.post("/api/v1/agents/nonexistent_agent_xyz/disable")
    assert response.status_code == 404
