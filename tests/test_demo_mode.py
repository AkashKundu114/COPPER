import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_reports_demo_mode(client):
    original = settings.COPPER_DEMO
    try:
        settings.COPPER_DEMO = True
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["demo_mode"] is True

        settings.COPPER_DEMO = False
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["demo_mode"] is False
    finally:
        settings.COPPER_DEMO = original


@pytest.mark.asyncio
async def test_demo_mode_chat_synthetic_response():
    from app.ai.orchestration.langchain_manager import langchain_manager

    original = settings.COPPER_DEMO
    try:
        settings.COPPER_DEMO = True
        messages = [{"role": "user", "content": "Hello COPPER"}]
        res = await langchain_manager.ainvoke(messages)
        assert "[DEMO MODE]" in res
        assert "Hello COPPER" in res
    finally:
        settings.COPPER_DEMO = original
