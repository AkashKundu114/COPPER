import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_tasks_crud_lifecycle():
    # 1. Create a task
    create_resp = client.post(
        "/api/v1/tasks",
        json={
            "title": "Build neural engine integration",
            "project": "COPPER Core",
            "priority": "high",
            "duration": "45m",
            "status": "planned",
        },
    )
    assert create_resp.status_code == 201
    task = create_resp.json()
    assert task["title"] == "Build neural engine integration"
    assert task["project"] == "COPPER Core"
    assert task["priority"] == "high"
    assert task["status"] == "planned"
    task_id = task["id"]

    # 2. Get task by ID
    get_resp = client.get(f"/api/v1/tasks/{task_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == task_id

    # 3. List tasks with filter
    list_resp = client.get("/api/v1/tasks?status=planned")
    assert list_resp.status_code == 200
    tasks = list_resp.json()
    assert any(t["id"] == task_id for t in tasks)

    # 4. Update task (PATCH)
    update_resp = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "completed", "priority": "low"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["status"] == "completed"
    assert updated["priority"] == "low"

    # 5. Delete task
    del_resp = client.delete(f"/api/v1/tasks/{task_id}")
    assert del_resp.status_code == 204

    # 6. Verify 404 after deletion
    get_after_del = client.get(f"/api/v1/tasks/{task_id}")
    assert get_after_del.status_code == 404


def test_tasks_validation_error():
    resp = client.post("/api/v1/tasks", json={"title": "   "})
    assert resp.status_code == 400


def test_projects_crud_lifecycle():
    # 1. Create a project
    create_resp = client.post(
        "/api/v1/projects",
        json={
            "name": "Project Aegis",
            "health": "healthy",
            "reason": "Tracking security telemetry.",
            "completed_tasks": 2,
            "total_tasks": 8,
        },
    )
    assert create_resp.status_code == 201
    proj = create_resp.json()
    assert proj["name"] == "Project Aegis"
    assert proj["health"] == "healthy"
    assert proj["completedTasks"] == 2
    assert proj["totalTasks"] == 8
    proj_id = proj["id"]

    # 2. Get project by ID
    get_resp = client.get(f"/api/v1/projects/{proj_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == proj_id

    # 3. List projects
    list_resp = client.get("/api/v1/projects")
    assert list_resp.status_code == 200
    assert any(p["id"] == proj_id for p in list_resp.json())

    # 4. Update project (increment tasks, change health)
    update_resp = client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"completed_tasks": 8, "health": "completed"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["completedTasks"] == 8
    assert update_resp.json()["health"] == "completed"

    # 5. Delete project
    del_resp = client.delete(f"/api/v1/projects/{proj_id}")
    assert del_resp.status_code == 204

    # 6. Verify 404 after deletion
    assert client.get(f"/api/v1/projects/{proj_id}").status_code == 404


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
