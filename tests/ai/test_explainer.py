import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.orchestration.agent_router import route_and_explain, route_message_detailed
from app.ai.orchestration.explainer import routing_history_store
from app.core.constants import AgentType
from app.main import app


@pytest.mark.asyncio
async def test_coding_explanation():
    prompt = "Write a python script to sort an array using quicksort"
    res, exp = await route_and_explain(prompt)

    assert res.agent == AgentType.CODING
    assert res.agent_type == AgentType.CODING
    assert res.explanation is not None

    assert exp["agent"] == "coding"
    assert exp["agent_codename"] == "AXIS"
    assert "AXIS" in exp["decision_summary"]
    assert "CODING" in exp["decision_summary"] or "coding" in exp["decision_summary"].lower()

    assert len(exp["matched_terms"]) > 0
    first_term = exp["matched_terms"][0]
    assert "term" in first_term
    assert "start" in first_term
    assert "end" in first_term
    assert prompt[first_term["start"] : first_term["end"]] == first_term["term"]

    assert len(exp["score_breakdown"]) > 0
    winner = exp["score_breakdown"][0]
    assert winner["is_winner"] is True
    assert winner["agent"] == "coding"
    assert winner["codename"] == "AXIS"

    calib = exp["confidence_calibration"]
    assert "raw_confidence" in calib
    assert "calibrated_confidence" in calib
    assert calib["certainty_tier"] in ["HIGH_CERTAINTY", "MODERATE_CERTAINTY", "AMBIGUOUS"]

    stages = exp["stage_progression"]
    assert len(stages) == 5
    stage_ids = [s["stage_id"] for s in stages]
    assert "learned_memory_cache" in stage_ids
    assert "fast_smalltalk_filter" in stage_ids
    assert "fast_pattern_scoring" in stage_ids
    assert "consequential_safety" in stage_ids
    assert "fallback_resolution" in stage_ids


@pytest.mark.asyncio
async def test_smalltalk_explanation():
    prompt = "Hello there! How are you today?"
    res = await route_message_detailed(prompt)

    assert res.agent == AgentType.CHAT
    exp = res.explanation
    assert exp is not None
    assert exp["route_stage"] in ("fast_smalltalk_filter", "default_conversational_fallback")
    assert exp["agent_codename"] in ("COPPER", "ATLAS")


@pytest.mark.asyncio
async def test_negative_rule_suppression_tracking():
    prompt = "Write a script to delete old temp files and clean directory"
    res = await route_message_detailed(prompt)

    exp = res.explanation
    assert exp is not None
    assert "suppressed_rules" in exp
    assert isinstance(exp["suppressed_rules"], list)


@pytest.mark.asyncio
async def test_consequential_safety_flag():
    prompt = "rm -rf / && drop table users"
    res = await route_message_detailed(prompt)

    assert res.is_consequential is True
    exp = res.explanation
    assert exp is not None
    assert exp["is_consequential"] is True
    assert exp["confidence_calibration"]["is_consequential"] is True

    safety_stage = next(s for s in exp["stage_progression"] if s["stage_id"] == "consequential_safety")
    assert "Consequential" in safety_stage["decision"] or "safety" in safety_stage["decision"].lower()


@pytest.mark.asyncio
async def test_routing_history_store():
    routing_history_store.clear()
    assert len(routing_history_store.get_history()) == 0

    prompt = "Debug this null pointer exception in python"
    await route_message_detailed(prompt)

    history = routing_history_store.get_history()
    assert len(history) == 1
    assert history[0]["agent"] == "coding"

    assert len(routing_history_store.get_history(agent_type="coding")) == 1
    assert len(routing_history_store.get_history(agent_type="vision")) == 0


@pytest.mark.asyncio
async def test_routing_analytics_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        hist_resp = await client.get("/api/v1/routing/history?limit=10")
        assert hist_resp.status_code == 200
        hist_data = hist_resp.json()
        assert "history" in hist_data
        assert isinstance(hist_data["history"], list)

        cm_resp = await client.get("/api/v1/routing/confusion-matrix")
        assert cm_resp.status_code == 200
        cm_data = cm_resp.json()
        assert "confusion_matrix" in cm_data
        assert "overall_accuracy_pct" in cm_data
        assert cm_data["overall_accuracy_pct"] >= 50.0

        cal_resp = await client.get("/api/v1/routing/confidence-calibration")
        assert cal_resp.status_code == 200
        cal_data = cal_resp.json()
        assert "calibration_bins" in cal_data
        assert "expected_calibration_error" in cal_data
        assert cal_data["is_well_calibrated"] is True
        assert len(cal_data["calibration_bins"]) == 10
