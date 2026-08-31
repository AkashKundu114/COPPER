from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.ai.orchestration.planner import PlanResult, SubTask
from app.main import app

client = TestClient(app)


def test_orchestration_plan_endpoint():
    mock_plan = PlanResult(
        is_decomposition=True,
        goal="Analyze CSV and create report",
        tasks=[
            SubTask(id="T1", agent="OMNI", instruction="Extract trends", depends_on=[]),
            SubTask(id="T2", agent="AXIS", instruction="Plot script", depends_on=["T1"]),
        ],
        synthesis={"agent": "CHAT", "instruction": "Synthesize results"},
        thinking="Decomposing into OMNI and AXIS",
    )

    with patch("app.ai.orchestration.planner.nexus_planner.plan", new_callable=AsyncMock) as mock_p:
        mock_p.return_value = mock_plan

        res = client.post(
            "/api/v1/orchestration/plan",
            json={"message": "Analyze CSV and plot trends", "context": ""},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_decomposition"] is True
        assert len(data["tasks"]) == 2
        assert data["tasks"][0]["agent"] == "OMNI"


def test_orchestration_traces_endpoint():
    res = client.get("/api/v1/orchestration/traces")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
