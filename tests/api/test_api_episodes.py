import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_episodes_list():
    response = client.get("/api/v1/episodes/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_episodes_list_with_context_filter():
    response = client.get("/api/v1/episodes/?context=Coding&limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_episodes_similar_search():
    response = client.get("/api/v1/episodes/similar?query=docker+networking")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_episodes_get_nonexistent():
    response = client.get("/api/v1/episodes/999999")
    assert response.status_code == 404
