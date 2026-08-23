from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_get_supported_documents():
    response = client.get("/api/v1/documents/supported")
    assert response.status_code == 200
    data = response.json()
    assert "supported_extensions" in data
    assert "pdf" in data["supported_extensions"]
    assert "csv" in data["supported_extensions"]
    assert "json" in data["supported_extensions"]
    assert "py" in data["supported_extensions"]
    assert data["total_supported"] >= 15


def test_parse_text_document():
    content = b"Hello world! This is a test text document for C.O.P.P.E.R."
    response = client.post(
        "/api/v1/documents/parse",
        files={"file": ("test_doc.txt", content, "text/plain")},
        data={"index_to_memory": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_doc.txt"
    assert data["extension"] == "txt"
    assert data["word_count"] == 10
    assert "Hello world!" in data["full_text"]
    assert data["status"] == "success"


def test_parse_csv_document():
    csv_content = b"name,role,level\nAlice,Engineer,Senior\nBob,Designer,Lead\nCharlie,Scientist,Staff"
    response = client.post(
        "/api/v1/documents/parse",
        files={"file": ("team.csv", csv_content, "text/csv")},
        data={"index_to_memory": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "team.csv"
    assert data["extension"] == "csv"
    assert data["structured_data"] is not None
    assert data["structured_data"]["headers"] == ["name", "role", "level"]
    assert data["structured_data"]["total_rows"] == 3


def test_parse_json_document():
    json_content = b'{"system": "COPPER", "version": "1.0", "modules": ["chat", "vision", "voice"]}'
    response = client.post(
        "/api/v1/documents/parse",
        files={"file": ("config.json", json_content, "application/json")},
        data={"index_to_memory": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "config.json"
    assert data["extension"] == "json"
    assert data["structured_data"] is not None
    assert "system" in data["structured_data"]["top_level_keys"]


def test_parse_empty_document():
    response = client.post(
        "/api/v1/documents/parse", files={"file": ("empty.txt", b"", "text/plain")}
    )
    assert response.status_code == 400
