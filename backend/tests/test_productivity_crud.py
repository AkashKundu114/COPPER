import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)




def test_schedule_events_crud_lifecycle():
    # 1. Create event under /schedule/events
    create_resp = client.post(
        "/api/v1/schedule/events",
        json={
            "time": "09:30 AM",
            "title": "Autonomous Agent Standup",
            "category": "Meeting",
            "completed": False,
        },
    )
    assert create_resp.status_code == 201
    event = create_resp.json()
    assert event["title"] == "Autonomous Agent Standup"
    assert event["time"] == "09:30 AM"
    assert event["completed"] is False
    event_id = event["id"]

    # 2. List events
    list_resp = client.get("/api/v1/schedule/events?category=Meeting")
    assert list_resp.status_code == 200
    assert any(e["id"] == event_id for e in list_resp.json())

    # 3. Direct /events route alias
    alias_get = client.get(f"/api/v1/events/{event_id}")
    assert alias_get.status_code == 200
    assert alias_get.json()["id"] == event_id

    # 4. Toggle completion
    patch_resp = client.patch(
        f"/api/v1/schedule/events/{event_id}",
        json={"completed": True},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["completed"] is True

    # 5. Delete event
    del_resp = client.delete(f"/api/v1/schedule/events/{event_id}")
    assert del_resp.status_code == 204
    assert client.get(f"/api/v1/schedule/events/{event_id}").status_code == 404


def test_epistemic_memory_crud_lifecycle():
    # 1. Create an epistemic memory
    create_resp = client.post(
        "/api/v1/memory",
        json={
            "content": "User prefers dark cybernetic UI styling with cyan accents",
            "type": "fact",
            "category": "User Preference",
            "confidence": 0.95,
            "evidence_count": 2,
        },
    )
    assert create_resp.status_code == 201
    mem = create_resp.json()
    assert "User prefers dark cybernetic" in mem["content"]
    assert mem["type"] == "fact"
    assert mem["category"] == "User Preference"
    assert mem["confidence"] == 0.95
    mem_id = mem["id"]

    # 2. Get memory by ID
    get_resp = client.get(f"/api/v1/memory/{mem_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == mem_id

    # 3. List memories with search filter
    search_resp = client.get("/api/v1/memory?search=cybernetic")
    assert search_resp.status_code == 200
    assert any(m["id"] == mem_id for m in search_resp.json())

    # 4. Profile endpoint includes facts
    profile_resp = client.get("/api/v1/memory/profile")
    assert profile_resp.status_code == 200
    assert "facts" in profile_resp.json()

    # 5. Update memory
    patch_resp = client.patch(
        f"/api/v1/memory/{mem_id}",
        json={"confidence": 0.99, "evidence_count": 3},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["confidence"] == 0.99
    assert patch_resp.json()["evidenceCount"] == 3

    # 6. Delete memory
    del_resp = client.delete(f"/api/v1/memory/{mem_id}")
    assert del_resp.status_code == 204
    assert client.get(f"/api/v1/memory/{mem_id}").status_code == 404
