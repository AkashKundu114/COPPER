from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_guardian_acknowledge_invalid_decision():
    response = client.post(
        "/api/v1/guardian/acknowledge",
        json={"session_id": "test_sid", "decision": "invalid_choice"},
    )
    assert response.status_code == 400


def test_guardian_confirm_invalid_text():
    response = client.post(
        "/api/v1/guardian/confirm",
        json={"session_id": "test_sid", "confirmation_text": "no"},
    )
    assert response.status_code == 400
