import asyncio
from datetime import datetime
import pytest

from app.ai.ambient.research_pipeline import research_pipeline
from app.ai.ambient.skill_learner import skill_learner
from app.ai.ambient.cognitive_load import cognitive_load_detector, CognitiveState
from app.ai.ambient.clipboard_monitor import ClipboardEntry
from app.ai.ambient.clipboard_processor import clipboard_processor
from app.ai.ambient.daily_briefing import DailyBriefingService
from app.ai.ambient.predictive_engine import PredictiveEngine
from app.ai.knowledge.causal_engine import causal_engine
from app.ai.companion.personality_manager import personality_manager
from app.ai.companion.accountability_tracker import accountability_tracker
from app.ai.companion.context_continuity import context_continuity


@pytest.mark.asyncio
async def test_research_pipeline_lifecycle():
    """Test starting, tracking, and retrieving research reports."""
    report = await research_pipeline.start_research(
        topic="Evaluate Microservices vs Monolith architectures",
        depth="quick",
        deadline="today",
    )
    assert report is not None
    assert report.report_id is not None
    assert report.topic == "Evaluate Microservices vs Monolith architectures"
    assert report.status in ["queued", "in_progress", "completed"]

    fetched = research_pipeline.get_report(report.report_id)
    assert fetched is not None
    assert fetched.report_id == report.report_id

    reports_list = research_pipeline.list_reports(limit=10)
    assert any(r.report_id == report.report_id for r in reports_list)


@pytest.mark.asyncio
async def test_skill_learner_extract_and_execute():
    """Test extracting reusable compositional skills and executing with params."""
    task_desc = "Sync local repository changes and create pull request"
    steps = [
        {"action": "git status", "status": "clean"},
        {"action": "git push origin main", "status": "success"},
        {"action": "gh pr create --title 'Feature' --body 'Auto'", "status": "merged"},
    ]
    result = {"status": "success", "pr_url": "https://github.com/org/repo/pull/42"}

    skill = skill_learner.extract_skill(task_desc, steps, result)
    assert skill is not None
    assert skill.skill_id is not None
    assert len(skill.steps) == 3
    assert skill.success_rate == 1.0

    # Test retrieval
    found = skill_learner.get_skill(skill.skill_id)
    assert found is not None
    assert found.name == skill.name

    # Test execution
    exec_res = await skill_learner.execute_skill(skill.skill_id, {"repo": "core"})
    assert exec_res["status"] == "success"
    assert exec_res["skill_id"] == skill.skill_id
    assert exec_res["use_count"] >= 1


def test_cognitive_load_suppresses_clipboard_processing():
    """Verify that DEEP_FOCUS suppresses active notifications and marks flow protection."""
    # Set deep focus
    cognitive_load_detector.current_state = CognitiveState.DEEP_FOCUS

    entry = ClipboardEntry(
        id="test-entry-1",
        timestamp=datetime.utcnow(),
        content="https://docs.astral.sh/uv/",
        content_type="url",
        content_preview="https://docs.astral.sh/uv/",
    )

    result = clipboard_processor.process_entry(entry)
    assert result["suppressed_for_focus"] is True
    assert result["notifications_suppressed"] is True

    # Set normal flow
    cognitive_load_detector.current_state = CognitiveState.NORMAL_FLOW
    result_normal = clipboard_processor.process_entry(entry)
    assert result_normal["suppressed_for_focus"] is False
    assert result_normal["notifications_suppressed"] is False


@pytest.mark.asyncio
async def test_context_watcher_feeds_daily_briefing():
    """Verify daily briefing pulls dynamic metrics from context watcher."""
    service = DailyBriefingService()
    morning = await service.generate_morning_briefing()
    assert morning is not None
    assert "yesterday_insight" in morning
    assert "Tracked" in morning["yesterday_insight"]

    eod = await service.generate_eod_summary()
    assert eod is not None
    assert "focus_time" in eod
    assert "context_switches" in eod
    assert "top_apps" in eod


def test_predictive_engine_ambient_integration():
    """Verify predictive engine includes context-watcher ambient patterns."""
    engine = PredictiveEngine()
    predictions = engine.analyze_patterns()
    assert isinstance(predictions, list)
    # Check if context_watcher_ambient prediction is registered
    ambient_preds = [p for p in engine._predictions if p.pattern_source == "context_watcher_ambient"]
    assert len(ambient_preds) >= 1


@pytest.mark.asyncio
async def test_causal_engine_auto_recording():
    """Verify causal engine event recording, querying, and link inference."""
    # Record task completion event
    event1 = causal_engine.record_event(
        description="Task completed: 'Optimize database indexes' (Project: Backend)",
        category="task_completion",
        source="task_manager",
        entities=["Backend"],
        metadata={"priority": "high"},
    )
    assert event1 is not None
    assert event1.event_id in causal_engine.events

    # Record meeting event
    event2 = causal_engine.record_event(
        description="Meeting concluded: 'Sprint Review' with 3 action items",
        category="meeting_conclusion",
        source="meeting_intelligence",
        entities=["Sprint Review"],
        metadata={"duration_seconds": 1800},
    )
    assert event2 is not None

    # Query why
    why = await causal_engine.query_why("Why was the database index task completed?")
    assert why is not None
    assert why.query == "Why was the database index task completed?"
    assert why.explanation is not None


def test_personality_manager_adaptation():
    """Test AI personality configuration and dynamic prompt adaptation."""
    personality_manager.update_config(warmth=0.9, formality=0.2, verbosity=0.3, code_first=True)
    assert personality_manager.config.warmth == 0.9
    assert personality_manager.config.formality == 0.2

    addon = personality_manager.get_system_prompt_addon()
    assert "Very warm" in addon or "Casual" in addon or "concise" in addon
    assert "Priority: Show code examples first" in addon

    # Test conversational adaptation heuristic
    personality_manager.adapt_from_message("hey dude thanks awesome work!")
    assert personality_manager.config.formality <= 0.25


def test_accountability_tracker():
    """Test accountability partner commitments, fulfillment, and score report."""
    commitment = accountability_tracker.add_commitment(
        title="Deploy v2.4 staging release",
        deadline="2026-09-12 18:00",
        urgency="high",
    )
    assert commitment.commitment_id is not None
    assert commitment.status == "pending"

    report_before = accountability_tracker.get_accountability_report()
    assert report_before["total_commitments"] >= 1

    fulfilled = accountability_tracker.fulfill_commitment(commitment.commitment_id)
    assert fulfilled is not None
    assert fulfilled.status == "fulfilled"

    report_after = accountability_tracker.get_accountability_report()
    assert report_after["fulfilled"] >= 1


def test_context_continuity_snapshots():
    """Test context continuity session handoff and resume prompt generation."""
    handoff = context_continuity.create_handoff(
        session_id="session-xyz-123",
        project="COPPER",
        decisions=["Adopted local differential privacy", "Integrated ambient research hub"],
        topics=["Multi-agent DAG orchestration", "Visual automation builder"],
        next_steps=["Deploy updated frontend", "Run full benchmark suite"],
        summary="Completed frontend and cross-system integration milestones.",
    )
    assert handoff.session_id == "session-xyz-123"

    latest = context_continuity.get_latest_handoff("COPPER")
    assert latest is not None
    assert latest.session_id == "session-xyz-123"

    prompt = context_continuity.generate_resume_prompt()
    assert "COPPER" in prompt or "Next steps" in prompt
