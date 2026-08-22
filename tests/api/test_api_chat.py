import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_message_empty_rejected():
    response = client.post("/api/v1/chat/message", json={"message": ""})
    assert response.status_code == 400


def test_chat_message_whitespace_rejected():
    response = client.post("/api/v1/chat/message", json={"message": "   "})
    assert response.status_code == 400


def test_chat_stream_empty_rejected():
    response = client.get("/api/v1/chat/stream?message=")
    assert response.status_code == 400


def test_chat_stream_whitespace_rejected():
    response = client.get("/api/v1/chat/stream?message=%20%20%20")
    assert response.status_code == 400


def test_chat_stream_valid_request():
    response = client.get("/api/v1/chat/stream?message=hello")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
