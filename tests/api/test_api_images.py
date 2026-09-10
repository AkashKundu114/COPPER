from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_image_engine_status():
    response = client.get("/api/v1/images/status")
    assert response.status_code == 200
    data = response.json()
    assert "model_path" in data
    assert "offline_only" in data
    assert data["offline_only"] is True


def test_image_generate_api():
    payload = {
        "prompt": "futuristic mechanical clock in copper and bronze",
        "width": 256,
        "height": 256,
        "steps": 1,
    }
    response = client.post("/api/v1/images/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("success", "fallback")
    assert "url" in data
    assert data["url"].startswith("/generated/copper_sd_")
    assert data["offline"] is True

    # Test static file retrieval through FastAPI static mount
    static_url = data["url"]
    static_res = client.get(static_url)
    assert static_res.status_code == 200
    assert static_res.headers["content-type"] == "image/png"


def test_image_unload_api():
    response = client.post("/api/v1/images/unload")
    assert response.status_code == 200
    data = response.json()
    assert "unloaded" in data
    assert "status" in data
