import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.ai.evaluation.improvement_tracker import improvement_tracker
from app.ai.evaluation.judge import crucible_judge
from app.ai.evaluation.prompt_optimizer import prompt_optimizer
from app.ai.llm.prompt_manager import clear_prompt_patches, get_prompt_patches_for_agent, get_system_prompt, register_prompt_patch
from app.core.constants import AgentType
from app.database.models.response_evaluation import EditStatus, FailureCategory, ProposedPromptEdit, ResponseEvaluation
from app.database.postgres import SessionLocal, init_db
from app.main import app


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()
    clear_prompt_patches()
    yield
    clear_prompt_patches()


def test_models_to_dict():
    ev = ResponseEvaluation(
        session_id="test_sess",
        user_message="How do I reverse a string in Python?",
        assistant_response="Use s[::-1]",
        agent_type="coding",
        accuracy=0.95,
        relevance=0.90,
        completeness=0.85,
        helpfulness=0.95,
        voice_consistency=0.90,
        overall_score=0.91,
        failures=[],
        reasoning="Accurate and concise.",
        improvement_suggestion=None,
    )
    d = ev.to_dict()
    assert d["agent_type"] == "coding"
    assert d["scores"]["accuracy"] == 0.95
    assert d["overall_score"] == 0.91
    assert d["failures"] == []

    edit = ProposedPromptEdit(
        agent_type="coding",
        failure_category="INCOMPLETE",
        failure_count=4,
        target_prompt_section="instructions",
        proposed_prompt_snippet="Always provide runnable code examples.",
        rationale="Prevents incomplete code snippets.",
        status=EditStatus.PENDING.value,
    )
    ed = edit.to_dict()
    assert ed["agent_type"] == "coding"
    assert ed["failure_category"] == "INCOMPLETE"
    assert ed["status"] == "pending"


def test_crucible_judge_parse_with_thinking():
    raw_deepseek_output = """
    <think>
    The user asked for string reversal.
    The response gave s[::-1].
    Accuracy is 1.0, relevance is 1.0, completeness is 0.8.
    </think>
    {
        "scores": {
            "accuracy": 0.95,
            "relevance": 0.95,
            "completeness": 0.80,
            "helpfulness": 0.90,
            "voice_consistency": 0.90
        },
        "overall": 0.90,
        "failures": ["INCOMPLETE"],
        "reasoning": "Accurate slice syntax but lacked explanatory context.",
        "improvement_suggestion": "Add a brief one-line explanation of slice step syntax."
    }
    """
    parsed = crucible_judge._parse_evaluation(raw_deepseek_output)
    assert parsed["accuracy"] == 0.95
    assert parsed["completeness"] == 0.80
    assert parsed["overall_score"] == 0.90
    assert "INCOMPLETE" in parsed["failures"]
    assert "Accurate slice syntax" in parsed["reasoning"]


def test_crucible_judge_heuristic_fallback():
    parsed = crucible_judge._heuristic_fallback(
        user_message="Explain recursion",
        assistant_response="Too short",
    )
    assert "INCOMPLETE" in parsed["failures"]
    assert parsed["overall_score"] <= 0.70


@pytest.mark.asyncio
async def test_crucible_judge_evaluate_turn_and_persist():
    db = SessionLocal()
    try:
        # Evaluate turn with mock or heuristic
        eval_record = await crucible_judge.evaluate_turn(
            user_message="What is the capital of France?",
            assistant_response="The capital of France is Paris. It is also the country's most populous city.",
            agent_type="chat",
            session_id="test_session_eval_1",
        )
        assert eval_record is not None
        assert eval_record.session_id == "test_session_eval_1"
        assert eval_record.agent_type == "chat"
        assert eval_record.overall_score >= 0.70

        # Verify DB presence
        fetched = db.query(ResponseEvaluation).filter(ResponseEvaluation.id == eval_record.id).first()
        assert fetched is not None
        assert fetched.session_id == "test_session_eval_1"
    finally:
        db.close()


def test_prompt_patches_and_injection():
    clear_prompt_patches()
    register_prompt_patch("coding", "Always ensure robust error handling and type hints.")
    register_prompt_patch("all", "Maintain concise technical precision.")

    patches = get_prompt_patches_for_agent("coding")
    assert "Always ensure robust error handling and type hints." in patches
    assert "Maintain concise technical precision." in patches

    prompt = get_system_prompt(AgentType.CODING)
    assert "CRUCIBLE OPTIMIZED DIRECTIVES:" in prompt
    assert "Always ensure robust error handling and type hints." in prompt
    assert "Maintain concise technical precision." in prompt


@pytest.mark.asyncio
async def test_prompt_optimizer_cluster_and_apply():
    db = SessionLocal()
    try:
        # Clear any prior test edits for research/VERBOSE to ensure idempotence
        db.query(ProposedPromptEdit).filter(
            ProposedPromptEdit.agent_type == "research",
            ProposedPromptEdit.failure_category == "VERBOSE",
        ).delete()
        db.commit()

        # Create 4 evaluations with VERBOSE failures for research agent
        for i in range(4):
            ev = ResponseEvaluation(
                session_id=f"verbose_test_{i}",
                user_message=f"Query {i}",
                assistant_response=f"Lengthy verbose output {i} " * 20,
                agent_type="research",
                accuracy=0.85,
                relevance=0.85,
                completeness=0.85,
                helpfulness=0.80,
                voice_consistency=0.85,
                overall_score=0.75,
                failures=["VERBOSE"],
                reasoning="Excessively wordy answer.",
            )
            db.add(ev)
        db.commit()

        # Run optimization cycle
        proposals = await prompt_optimizer.run_optimization_cycle()
        assert len(proposals) >= 1
        verbose_prop = next(p for p in proposals if p["agent_type"] == "research" and p["failure_category"] == "VERBOSE")
        assert verbose_prop["failure_count"] >= 4
        assert verbose_prop["status"] == "pending"

        # Apply the proposed edit
        edit_id = verbose_prop["id"]
        res = await prompt_optimizer.apply_proposed_edit(edit_id)
        assert res["success"] is True
        assert res["benchmark_before"] > 0
        assert res["benchmark_after"] > 0
        assert res["regression_detected"] is False

        # Verify DB updated
        applied_edit = db.query(ProposedPromptEdit).filter(ProposedPromptEdit.id == edit_id).first()
        assert applied_edit.status == "applied"
        assert applied_edit.applied_at is not None

        # Verify prompt patch was registered
        patches = get_prompt_patches_for_agent("research")
        assert any(applied_edit.proposed_prompt_snippet in p for p in patches)
    finally:
        db.close()


def test_improvement_tracker_metrics():
    metrics = improvement_tracker.get_rolling_metrics(days=7)
    assert "overall_score" in metrics
    assert "dimensions" in metrics
    assert "accuracy" in metrics["dimensions"]
    assert "relevance" in metrics["dimensions"]
    assert "completeness" in metrics["dimensions"]
    assert "helpfulness" in metrics["dimensions"]
    assert "voice_consistency" in metrics["dimensions"]
    assert "trend_direction" in metrics
    assert "daily_history" in metrics

    failures = improvement_tracker.get_failures_analysis(limit=10)
    assert "category_counts" in failures
    assert "recent_failures" in failures

    edits = improvement_tracker.get_proposed_edits()
    assert isinstance(edits, list)


def test_self_improvement_api_endpoints():
    client = TestClient(app)

    # 1. GET /api/v1/self-improvement/metrics
    r_metrics = client.get("/api/v1/self-improvement/metrics?days=7")
    assert r_metrics.status_code == 200
    data = r_metrics.json()
    assert "overall_score" in data
    assert "dimensions" in data

    # 2. GET /api/v1/self-improvement/failures
    r_failures = client.get("/api/v1/self-improvement/failures?limit=10")
    assert r_failures.status_code == 200
    fdata = r_failures.json()
    assert "category_counts" in fdata

    # 3. GET /api/v1/self-improvement/proposed-edits
    r_edits = client.get("/api/v1/self-improvement/proposed-edits")
    assert r_edits.status_code == 200
    assert isinstance(r_edits.json(), list)

    # 4. POST /api/v1/self-improvement/optimize-prompts
    r_opt = client.post("/api/v1/self-improvement/optimize-prompts")
    assert r_opt.status_code == 200
    assert r_opt.json()["status"] == "success"

    # 5. POST /api/v1/self-improvement/run-benchmark
    r_bench = client.post("/api/v1/self-improvement/run-benchmark")
    assert r_bench.status_code == 200
    bdata = r_bench.json()
    assert bdata["status"] == "success"
    assert bdata["summary"]["routing_accuracy_pct"] >= 95.0
    assert bdata["summary"]["guardian_threat_catch_pct"] == 100.0


def test_model_selection_optimization():
    from app.ai.evaluation.model_optimizer import model_optimizer
    from app.ai.llm.ollama_client import ollama_client

    # Record 3 high-quality turns for deepseek-r1:7b on coding agent
    for _ in range(3):
        model_optimizer.record_turn_performance(
            agent_type="coding",
            model_name="deepseek-r1:7b",
            quality_score=0.98,
            latency_ms=250.0,
            has_failure=False,
        )

    # Verify optimal model promoted
    optimal = model_optimizer.get_optimal_model("coding")
    assert optimal == "deepseek-r1:7b"

    # Verify select_model routes to the optimal model
    selected = ollama_client.select_model(AgentType.CODING)
    assert selected == "deepseek-r1:7b"

    # Verify model rankings endpoint returns metrics
    client = TestClient(app)
    r = client.get("/api/v1/self-improvement/model-rankings")
    assert r.status_code == 200
    rankings = r.json()
    assert any(rank["model_name"] == "deepseek-r1:7b" for rank in rankings)

