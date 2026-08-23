from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_audit_list():
    response = client.get("/api/v1/audit/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_audit_export():
    response = client.get("/api/v1/audit/export")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")


def test_audit_delete_all_without_confirm():
    response = client.post("/api/v1/audit/delete-all", json={"confirm": False})
    assert response.status_code == 400
