import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.vision_service import vision_service
from app.ai.memory.persistent_memory import persistent_memory

client = TestClient(app)


@pytest.mark.asyncio
async def test_vision_service_observe_frame():
    # 1x1 transparent PNG base64
    dummy_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    res_cam = await vision_service.observe_frame(dummy_b64, source="camera")
    assert "observation" in res_cam
    assert res_cam["source"] == "camera"
    assert persistent_memory.get_preference("latest_vision_observation") is not None

    res_screen = await vision_service.observe_frame(dummy_b64, source="screen")
    assert "observation" in res_screen
    assert res_screen["source"] == "screen"


def test_vision_api_observe_endpoint():
    dummy_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    resp = client.post(
        "/api/v1/vision/observe",
        json={"image_base64": dummy_b64, "source": "camera"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "observation" in data
    assert data["source"] == "camera"
