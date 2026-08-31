from app.main import app
from fastapi.testclient import TestClient

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


def test_chat_message_includes_telemetry_metrics():
    response = client.post("/api/v1/chat/message", json={"message": "hello test"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "metrics" in data
    if data["metrics"] is not None:
        metrics = data["metrics"]
        assert "model" in metrics
        assert "prompt_tokens" in metrics
        assert "completion_tokens" in metrics
        assert "total_tokens" in metrics
        assert "tokens_per_sec" in metrics
        assert "ttft_ms" in metrics
        assert "total_time_sec" in metrics
        assert metrics["total_tokens"] == metrics["prompt_tokens"] + metrics["completion_tokens"]
