import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_document_templates():
    res = client.get("/api/v1/documents/templates")
    assert res.status_code == 200
    data = res.json()
    assert "templates" in data
    assert "technical_report" in data["templates"]


def test_get_supported_extensions():
    res = client.get("/api/v1/documents/supported")
    assert res.status_code == 200
    data = res.json()
    assert "pdf" in data["supported_extensions"]
    assert "docx" in data["supported_extensions"]


def test_generate_document_api():
    payload = {
        "title": "API Test PDF Report",
        "format": "pdf",
        "template_type": "technical_report",
        "sections": [
            {"heading": "Introduction", "content": "This is a test PDF."},
            {"heading": "Key Points", "bullets": ["Fast", "Autonomous", "Low VRAM"]},
        ],
        "index_to_memory": False,
    }
    res = client.post("/api/v1/documents/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "document" in data
    filename = data["document"]["filename"]

    # Test download endpoint
    dl_res = client.get(f"/api/v1/documents/download/{filename}")
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 50


def test_list_generated_documents():
    res = client.get("/api/v1/documents/generated")
    assert res.status_code == 200
    data = res.json()
    assert "documents" in data
    assert "total" in data
