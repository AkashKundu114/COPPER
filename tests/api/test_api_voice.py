from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_voice_status():
    response = client.get("/api/v1/voice/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "tts_voices" in data


def test_voice_models():
    response = client.get("/api/v1/voice/models")
    assert response.status_code == 200
    data = response.json()
    assert "whisper_models" in data
    assert "tts_voices" in data


def test_voice_voices():
    response = client.get("/api/v1/voice/voices")
    assert response.status_code == 200
    data = response.json()
    assert "voices" in data
    assert len(data["voices"]) >= 2


def test_voice_synthesize_success():
    response = client.post(
        "/api/v1/voice/synthesize",
        json={"text": "Voice test speech audio", "voice": "copper_synth", "speed": 1.0},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 44


def test_voice_synthesize_empty_text():
    response = client.post(
        "/api/v1/voice/synthesize",
        json={"text": "", "voice": "copper_synth", "speed": 1.0},
    )
    assert response.status_code == 400


def test_voice_transcribe_empty_file():
    response = client.post(
        "/api/v1/voice/transcribe", files={"audio": ("empty.wav", b"", "audio/wav")}
    )
    assert response.status_code in [200, 400, 422]
