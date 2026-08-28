import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.models.self_memory import SelfMemory, SelfMemoryCategory, SelfMemoryOutcome
from app.services.self_model_service import self_model_service
from app.ai.llm.prompt_manager import get_system_prompt, get_mode_prompt, BASE_COPPER_SYSTEM_PROMPT
from app.core.constants import AgentType

client = TestClient(app)


def test_base_prompt_consciousness_content():
    assert "WHO YOU ARE" in BASE_COPPER_SYSTEM_PROMPT
    assert "HOW YOU THINK OUT LOUD" in BASE_COPPER_SYSTEM_PROMPT
    assert "HOW YOU CHANGE" in BASE_COPPER_SYSTEM_PROMPT
    assert "BOUNDARIES THAT DON'T BEND" in BASE_COPPER_SYSTEM_PROMPT
    assert "{self_context_snippet}" in BASE_COPPER_SYSTEM_PROMPT


def test_prompt_manager_self_context_injection():
    self_ctx = "- [DECISION] Recommended Polars over Pandas (confidence: 85%, evidence: 3x)"
    prompt = get_system_prompt(AgentType.CODING, memory_context="User prefers Python", self_context=self_ctx)
    assert self_ctx in prompt
    assert "Agent Role: CODING" in prompt
    assert "User prefers Python" in prompt


def test_get_mode_prompts():
    for mode in ['reasoning', 'coding', 'research', 'fast', 'auto']:
        prompt = get_mode_prompt(mode, memory_context="User context", self_context="Self context")
        assert "Self context" in prompt
        assert "User context" in prompt
        if mode == 'reasoning':
            assert "<think>" in prompt


def test_correction_detection():
    assert self_model_service.detect_correction("no, that's wrong, I asked for FastAPI")
    assert self_model_service.detect_correction("actually I prefer pytest over unittest")
    assert self_model_service.detect_correction("don't do it that way")
    assert not self_model_service.detect_correction("Please write a function to parse CSV")


@pytest.mark.asyncio
async def test_self_memory_lifecycle():
    entry = await self_model_service._create_entry(
        category=SelfMemoryCategory.DECISION,
        content='Recommended async PostgreSQL  connection pool',
        confidence=0.5
    )
    assert entry is not None
    assert entry.id is not None
    assert entry.confidence == 0.5

    success = self_model_service.apply_bayesian_update(entry.id)
    assert success is True

    all_memories = self_model_service.get_all(category='decision')
    ids = [m['id'] for m in all_memories]
    assert entry.id in ids

    res = self_model_service.resolve(entry.id)
    assert res is True

    ctx = await self_model_service.build_self_context('PostgreSQL')
    assert isinstance(ctx, str)


def test_self_memory_api_endpoints():
    response = client.get('/api/v1/self-memory')
    assert response.status_code == 200
    data = response.json()
    assert 'data' in data
    assert isinstance(data['data'], list)

    response = client.get('/api/v1/self-memory?category=decision&limit=10')
    assert response.status_code == 200
    assert 'data' in response.json()

    response = client.post('/api/v1/self-memory/non_existent_uuid/resolve')
    assert response.status_code == 404
