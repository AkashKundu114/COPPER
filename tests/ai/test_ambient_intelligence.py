import pytest
import uuid
from datetime import datetime, UTC

from app.ai.ambient.context_watcher import context_watcher, ActivityEntry, ActivitySession
from app.ai.ambient.activity_timeline import activity_timeline
from app.ai.ambient.daily_briefing import daily_briefing_service
from app.ai.ambient.clipboard_monitor import clipboard_monitor, ClipboardEntry
from app.ai.ambient.clipboard_processor import clipboard_processor
from app.ai.ambient.cognitive_load import cognitive_load_detector, CognitiveState
from app.ai.ambient.context_switcher import context_switcher
from app.ai.ambient.predictive_engine import predictive_engine
from app.ai.ambient.meeting_intelligence import meeting_intelligence


def test_context_watcher_record_and_timeline():
    now = datetime.now()
    entry = ActivityEntry(
        app_name="Code.exe",
        window_title="main.py - COPPER - Visual Studio Code",
        timestamp=now,
        duration_seconds=5.0
    )
    context_watcher.buffer.append(entry)
    timeline = context_watcher.get_timeline(hours=1)
    assert isinstance(timeline, list)
    assert len(timeline) > 0
    assert timeline[-1].app_name == "Code.exe"


def test_activity_timeline_aggregation():
    stats = activity_timeline.get_productivity_stats(hours=24)
    assert isinstance(stats, dict)
    assert "focus_time_minutes" in stats
    assert "context_switches" in stats

    summary = activity_timeline.get_daily_summary()
    assert isinstance(summary, str)


@pytest.mark.asyncio
async def test_daily_briefing_synthesis():
    briefing = await daily_briefing_service.generate_morning_briefing()
    assert briefing is not None
    assert isinstance(briefing, dict)

    eod = await daily_briefing_service.generate_eod_summary()
    assert eod is not None
    assert isinstance(eod, dict)


def test_clipboard_processor_classification():
    # URL
    t_url = clipboard_monitor.detect_type("https://github.com/AkashKundu114/COPPER")
    assert t_url == "url"

    entry_url = ClipboardEntry(
        id=uuid.uuid4().hex,
        timestamp=datetime.now(UTC),
        content="https://github.com/AkashKundu114/COPPER",
        content_type=t_url,
        content_preview="https://github.com/AkashKundu114/COPPER"
    )
    proc_url = clipboard_processor.process_entry(entry_url)
    assert "suggested_actions" in proc_url
    assert any("browser" in a.lower() or "save" in a.lower() for a in proc_url["suggested_actions"])

    # Code
    code_text = "def quicksort(arr):\n    return arr if len(arr) <= 1 else arr"
    t_code = clipboard_monitor.detect_type(code_text)
    assert t_code == "code"

    entry_code = ClipboardEntry(
        id=uuid.uuid4().hex,
        timestamp=datetime.now(UTC),
        content=code_text,
        content_type=t_code,
        content_preview=code_text
    )
    proc_code = clipboard_processor.process_entry(entry_code)
    assert "suggested_actions" in proc_code

    # Email
    assert clipboard_monitor.detect_type("contact@copper-ai.local") == "email"

    # JSON
    assert clipboard_monitor.detect_type('{"status": "online", "nodes": 4}') == "json"


def test_cognitive_load_detector():
    for state in CognitiveState:
        recs = cognitive_load_detector.get_recommendations(state)
        assert isinstance(recs, list)
        assert len(recs) > 0

    profile = cognitive_load_detector.detect_state()
    assert profile is not None
    assert profile.state in CognitiveState
    assert 0.0 <= profile.confidence <= 1.0


def test_context_switcher_project_detection_and_switch():
    title = "backend/app/main.py - COPPER - Cursor"
    project = context_switcher.detect_project_switch("Cursor.exe", title)
    assert project is not None
    assert "COPPER" in project or "backend" in project

    switched = context_switcher.switch_to("TestProject")
    assert switched is not None
    assert switched.project_name == "TestProject"

    parked = context_switcher.park_current()
    assert parked is not None
    assert parked.project_name == "TestProject"


def test_predictive_engine_mining():
    predictions = predictive_engine.analyze_patterns()
    assert isinstance(predictions, list)
    all_patterns = predictive_engine.get_all_patterns()
    assert isinstance(all_patterns, list)


@pytest.mark.asyncio
async def test_meeting_intelligence_structure_notes():
    raw_transcript = (
        "Alice: Let us review the Q3 roadmap. Bob will handle database indexing by Friday. "
        "Charlie: I will finalize the differential privacy budget configuration. "
        "Alice: Great, meeting adjourned."
    )
    notes = await meeting_intelligence._generate_structured_notes(raw_transcript)
    assert notes is not None
    assert isinstance(notes, dict)
    assert "summary" in notes or "decisions" in notes or "action_items" in notes
