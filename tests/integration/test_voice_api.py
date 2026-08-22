import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_voice_status_endpoint():
    response = client.get("/api/v1/voice/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "tts_voices" in data


def test_voice_models_endpoint():
    response = client.get("/api/v1/voice/models")
    assert response.status_code == 200
    data = response.json()
    assert "whisper_models" in data
    assert "tts_voices" in data


def test_voice_voices_endpoint():
    response = client.get("/api/v1/voice/voices")
    assert response.status_code == 200
    data = response.json()
    assert "voices" in data
    assert len(data["voices"]) > 0


def test_voice_synthesize_endpoint():
    response = client.post(
        "/api/v1/voice/synthesize",
        json={"text": "Testing text to speech synthesis.", "voice": "copper_synth", "speed": 1.0},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 44
