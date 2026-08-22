import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_system_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "COPPER"
    assert data["status"] == "online"


def test_system_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_system_openapi_spec():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data
    assert "/api/v1/chat/message" in data["paths"]


def test_system_404_not_found():
    response = client.get("/api/v1/nonexistent_route_404")
    assert response.status_code == 404


def test_system_405_method_not_allowed():
    response = client.post("/health")
    assert response.status_code == 405


def test_system_cors_headers():
    response = client.options(
        "/api/v1/voice/status",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_system_gzip_middleware_large_response():
    response = client.get("/openapi.json", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
