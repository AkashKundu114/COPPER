import pytest
import uuid
from datetime import datetime, timezone

from app.ai.companion.personality_manager import personality_manager
from app.ai.companion.accountability_tracker import accountability_tracker
from app.ai.companion.context_continuity import context_continuity
from app.ai.companion.skill_gap_detector import skill_gap_detector
from app.ai.os_integration.notification_filter import notification_filter
from app.ai.os_integration.plugin_manager import plugin_manager
from app.ai.os_integration.device_sync import device_sync


def test_personality_manager():
    # Save original warmth
    orig_warmth = personality_manager.config.warmth

    # Update config
    personality_manager.update_config(warmth=0.9, formality=0.2, verbosity=0.3)
    assert personality_manager.config.warmth == 0.9

    addon = personality_manager.get_system_prompt_addon()
    assert isinstance(addon, str)
    assert "warm" in addon.lower()

    # Adapt from message
    personality_manager.adapt_from_message("hey thanks cool awesome dude lol")
    assert personality_manager.config.formality <= 0.2

    # Restore
    personality_manager.update_config(warmth=orig_warmth)


def test_accountability_tracker():
    deadline = "2026-12-31T23:59:59Z"
    comm = accountability_tracker.add_commitment(
        title=f"Complete COPPER AI OS release {uuid.uuid4()}",
        deadline=deadline,
        urgency="high"
    )
    assert comm is not None
    assert comm.status == "pending"

    # Fulfill
    fulfilled = accountability_tracker.fulfill_commitment(comm.commitment_id)
    assert fulfilled is not None
    assert fulfilled.status == "fulfilled"

    # Report
    report = accountability_tracker.get_accountability_report()
    assert "total_commitments" in report
    assert "follow_through_rate_pct" in report


def test_context_continuity():
    sess_id = str(uuid.uuid4())
    handoff = context_continuity.create_handoff(
        session_id=sess_id,
        project="COPPER-AI-OS",
        decisions=["Implemented Differential Privacy", "Integrated Causal Graph"],
        topics=["Memory Provenance", "Plugin Registry"],
        next_steps=["Run verification", "Prepare release tag"],
        summary="Completed Tier 1-5 features and full test coverage."
    )
    assert handoff is not None
    assert handoff.session_id == sess_id

    latest = context_continuity.get_latest_handoff(project="COPPER-AI-OS")
    assert latest is not None
    assert latest.active_project == "COPPER-AI-OS"

    resume_prompt = context_continuity.generate_resume_prompt()
    assert isinstance(resume_prompt, str)
    assert "COPPER-AI-OS" in resume_prompt


def test_skill_gap_detector():
    topic = f"asyncio-distributed-locks-{uuid.uuid4()}"
    skill_gap_detector.record_query_topic(topic)
    skill_gap_detector.record_query_topic(topic)
    skill_gap_detector.record_query_topic(topic)

    gaps = skill_gap_detector.get_active_gaps()
    target_gap = next((g for g in gaps if g.topic == topic), None)
    assert target_gap is not None
    assert target_gap.query_count >= 3
    assert target_gap.recommended_guide is not None

    status_ok = skill_gap_detector.mark_gap_status(target_gap.gap_id, "resolved")
    assert status_ok is True


def test_notification_filter():
    notif = notification_filter.post_notification(
        source="build_system",
        title="Critical compilation alert",
        message="Urgent: high memory threshold reached"
    )
    assert notif is not None
    assert notif.category == "urgent"

    all_notifs = notification_filter.get_notifications()
    assert len(all_notifs) > 0

    digest = notification_filter.generate_digest()
    assert "summary" in digest
    assert "counts" in digest


def test_plugin_manager():
    plugins = plugin_manager.list_plugins()
    assert isinstance(plugins, list)
    assert len(plugins) >= 1

    # Test toggling
    pid = plugins[0].id
    orig_state = plugins[0].enabled
    toggled = plugin_manager.toggle_plugin(pid, not orig_state)
    assert toggled is not None
    assert toggled.enabled == (not orig_state)

    # Restore
    plugin_manager.toggle_plugin(pid, orig_state)

    tools = plugin_manager.get_registered_tools()
    assert isinstance(tools, list)


def test_device_sync():
    payload = device_sync.generate_handoff_payload(device_name="Workstation-Alpha")
    assert payload is not None
    assert payload.checksum is not None
    assert payload.device_name == "Workstation-Alpha"

    # Convert to dict and receive
    payload_dict = {
        "payload_id": payload.payload_id,
        "device_id": payload.device_id,
        "device_name": payload.device_name,
        "timestamp": payload.timestamp,
        "active_project": payload.active_project,
        "recent_tasks": payload.recent_tasks,
        "unresolved_queries": payload.unresolved_queries,
        "memory_hash": payload.memory_hash,
        "checksum": payload.checksum
    }
    result = device_sync.receive_handoff_payload(payload_dict)
    assert result["status"] == "success"

    status = device_sync.get_sync_status()
    assert status["sync_health"] == "healthy"
    assert status["current_device"] is not None
