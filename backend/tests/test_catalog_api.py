from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_catalog_summary():
    response = client.get("/api/v1/catalog/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_personas"] == 264
    assert data["total_divisions"] == 18
    assert data["total_scientific_skills"] == 165
    assert data["total_tools"] == 36
    assert len(data["divisions"]) == 18


def test_catalog_personas_list_and_filter():
    # Test all personas (paginated)
    response = client.get("/api/v1/catalog/personas?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 264
    assert len(data["personas"]) == 10

    # Test division filter
    response_eng = client.get("/api/v1/catalog/personas?division=engineering&limit=100")
    assert response_eng.status_code == 200
    data_eng = response_eng.json()
    assert data_eng["total"] == 64
    assert all(p["division"] == "engineering" for p in data_eng["personas"])

    # Test search
    response_search = client.get("/api/v1/catalog/personas?search=architect")
    assert response_search.status_code == 200
    data_search = response_search.json()
    assert data_search["total"] > 0


def test_catalog_persona_detail():
    response = client.get("/api/v1/catalog/personas/engineering:engineering-software-architect")
    assert response.status_code == 200
    p = response.json()
    assert p["name"] == "Software Architect"
    assert "system_prompt" in p
    assert len(p["system_prompt"]) > 100


def test_catalog_scientific_skills():
    response = client.get("/api/v1/catalog/scientific-skills?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 165
    assert len(data["skills"]) == 10

    # Test detail
    skill_resp = client.get("/api/v1/catalog/scientific-skills/biopython")
    assert skill_resp.status_code == 200
    skill = skill_resp.json()
    assert "instructions" in skill


def test_catalog_tools():
    response = client.get("/api/v1/catalog/tools")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 36
    tool_names = [t["name"] for t in data["tools"]]
    assert "codebase_map" in tool_names
    assert "scrapling_scrape" in tool_names
    assert "arxiv_search" in tool_names
    assert "workflow_diagram_render" in tool_names
    assert "video_create_slideshow" in tool_names
