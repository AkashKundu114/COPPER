import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_ambient_endpoints():
    res_timeline = client.get("/api/v1/ambient/timeline")
    assert res_timeline.status_code == 200
    assert isinstance(res_timeline.json(), list)

    res_stats = client.get("/api/v1/ambient/stats")
    assert res_stats.status_code == 200
    assert "focus_time_minutes" in res_stats.json()


def test_api_briefing_endpoints():
    res_morning = client.get("/api/v1/briefing/morning")
    assert res_morning.status_code == 200

    res_eod = client.get("/api/v1/briefing/eod")
    assert res_eod.status_code == 200


def test_api_cognitive_endpoints():
    res_state = client.get("/api/v1/cognitive/state")
    assert res_state.status_code == 200
    data = res_state.json()
    assert "state" in data
    assert "confidence" in data

    res_suppress = client.get("/api/v1/cognitive/should-suppress")
    assert res_suppress.status_code == 200
    assert "suppress" in res_suppress.json()


def test_api_privacy_endpoints():
    res_budget = client.get("/api/v1/privacy/budget")
    assert res_budget.status_code == 200
    assert "epsilon" in res_budget.json()

    res_guarantee = client.get("/api/v1/privacy/guarantee")
    assert res_guarantee.status_code == 200
    assert "guarantee" in res_guarantee.json()

    res_demo = client.post("/api/v1/privacy/noise-demo", json={"embedding": [0.1, 0.2, 0.3]})
    assert res_demo.status_code == 200
    data = res_demo.json()
    assert "original" in data
    assert "noised" in data


def test_api_causal_endpoints():
    evt_payload = {
        "description": "API test event",
        "category": "system",
        "source": "pytest",
        "entities": ["test_runner"],
        "metadata": {}
    }
    res_create = client.post("/api/v1/causal/events", json=evt_payload)
    assert res_create.status_code == 200
    assert res_create.json()["status"] == "success"

    res_list = client.get("/api/v1/causal/events")
    assert res_list.status_code == 200
    assert res_list.json()["status"] == "success"


def test_api_provenance_endpoints():
    fact_payload = {
        "fact": f"COPPER is tested via pytest {uuid.uuid4()}",
        "source_type": "automated_test",
        "source_id": "test_api_nextgen_routes",
        "confidence": 0.95
    }
    res_post = client.post("/api/v1/provenance/facts", json=fact_payload)
    assert res_post.status_code == 201
    data = res_post.json()
    assert data["fact"] == fact_payload["fact"]

    res_list = client.get("/api/v1/provenance/facts")
    assert res_list.status_code == 200
    assert isinstance(res_list.json(), list)


def test_api_personality_endpoints():
    res_config = client.get("/api/v1/personality/config")
    assert res_config.status_code == 200
    assert "warmth" in res_config.json()

    res_prompt = client.get("/api/v1/personality/prompt-addon")
    assert res_prompt.status_code == 200
    assert "prompt_addon" in res_prompt.json()


def test_api_accountability_endpoints():
    res_list = client.get("/api/v1/accountability/commitments")
    assert res_list.status_code == 200
    assert isinstance(res_list.json(), list)

    res_report = client.get("/api/v1/accountability/report")
    assert res_report.status_code == 200
    assert "total_commitments" in res_report.json()


def test_api_continuity_endpoints():
    res_prompt = client.get("/api/v1/continuity/resume-prompt")
    assert res_prompt.status_code == 200
    assert "prompt" in res_prompt.json()


def test_api_skill_gaps_endpoints():
    res_list = client.get("/api/v1/skill-gaps")
    assert res_list.status_code == 200
    assert isinstance(res_list.json(), list)

    res_record = client.post("/api/v1/skill-gaps/record", json={"topic": f"api_test_topic_{uuid.uuid4()}"})
    assert res_record.status_code == 200
    assert res_record.json()["status"] == "recorded"


def test_api_plugins_endpoints():
    res_plugins = client.get("/api/v1/plugins")
    assert res_plugins.status_code == 200
    assert isinstance(res_plugins.json(), list)

    res_tools = client.get("/api/v1/plugins/tools")
    assert res_tools.status_code == 200
    assert isinstance(res_tools.json(), list)


def test_api_notifications_endpoints():
    res_notifs = client.get("/api/v1/notifications")
    assert res_notifs.status_code == 200
    assert isinstance(res_notifs.json(), list)

    res_digest = client.get("/api/v1/notifications/digest")
    assert res_digest.status_code == 200
    assert "summary" in res_digest.json()


def test_api_sync_endpoints():
    res_status = client.get("/api/v1/sync/status")
    assert res_status.status_code == 200
    assert "sync_health" in res_status.json()

    res_handoff = client.post("/api/v1/sync/handoff")
    assert res_handoff.status_code == 200
    assert "checksum" in res_handoff.json()
