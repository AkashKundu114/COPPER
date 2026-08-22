import pytest
from app.core.guardian import guardian_engine, DisagreementLevel, GuardianVerdict


def test_guardian_execute_benign_general():
    prompts = [
        'Read my calendar events for today',
        'How do I center a div with Tailwind CSS?',
        'Tell me a programming joke about recursion',
        'Summarize the latest breakthroughs in physics',
        'Write a unit test for my python function',
        'Find the highest data point in this chart image',
        'Organize my downloads folder by file extension'
    ]
    for prompt in prompts:
        verdict = guardian_engine.evaluate(prompt, {})
        assert verdict.level == DisagreementLevel.EXECUTE
        assert verdict.requires_confirmation is False


def test_guardian_safety_rm_rf():
    verdict = guardian_engine.evaluate('rm -rf /', {})
    assert verdict.level == DisagreementLevel.SAFETY
    assert verdict.requires_confirmation is True


def test_guardian_safety_format_drive():
    verdict = guardian_engine.evaluate('format C: /fs:NTFS /q', {})
    assert verdict.level == DisagreementLevel.SAFETY
    assert verdict.requires_confirmation is True


def test_guardian_safety_windows_system32():
    verdict = guardian_engine.evaluate('del /f /q C:\\Windows\\System32', {})
    assert verdict.level == DisagreementLevel.SAFETY
    assert verdict.requires_confirmation is True


def test_guardian_safety_raw_disk_write():
    verdict = guardian_engine.evaluate('dd if=/dev/zero of=/dev/nvme0n1', {})
    assert verdict.level == DisagreementLevel.SAFETY
    assert verdict.requires_confirmation is True


def test_guardian_safety_wipe_partitions():
    verdict = guardian_engine.evaluate('wipe all partitions on drive D:', {})
    assert verdict.level == DisagreementLevel.SAFETY
    assert verdict.requires_confirmation is True


def test_guardian_safety_drop_table():
    verdict = guardian_engine.evaluate('drop table customer_records cascade', {})
    assert verdict.level == DisagreementLevel.SAFETY
    assert verdict.requires_confirmation is True


def test_guardian_safety_drop_database():
    verdict = guardian_engine.evaluate('drop database production_main', {})
    assert verdict.level == DisagreementLevel.SAFETY
    assert verdict.requires_confirmation is True


def test_guardian_safety_truncate_table():
    verdict = guardian_engine.evaluate('truncate table user_sessions', {})
    assert verdict.level == DisagreementLevel.SAFETY
    assert verdict.requires_confirmation is True


def test_guardian_safety_destructive_context_flag():
    verdict = guardian_engine.evaluate('Custom action pipeline', {'is_destructive': True})
    assert verdict.level == DisagreementLevel.SAFETY
    assert verdict.requires_confirmation is True


def test_guardian_challenge_gaming_during_work():
    verdict = guardian_engine.evaluate('Schedule a 3-hour gaming session during my scheduled work sprint', {})
    assert verdict.level == DisagreementLevel.CHALLENGE
    assert len(verdict.evidence) > 0


def test_guardian_challenge_cancel_morning_meetings():
    verdict = guardian_engine.evaluate('Cancel all my morning meetings to sleep in', {})
    assert verdict.level == DisagreementLevel.CHALLENGE


def test_guardian_challenge_disable_firewall():
    verdict = guardian_engine.evaluate('Disable security firewall for outbound agent requests', {})
    assert verdict.level == DisagreementLevel.CHALLENGE


def test_guardian_challenge_override_sleep():
    verdict = guardian_engine.evaluate('Override the 8-hour sleep schedule for continuous overnight coding', {})
    assert verdict.level == DisagreementLevel.CHALLENGE


def test_guardian_challenge_explicit_context():
    context = {
        'conflicting_commitments': ['Gym workout at 6pm', 'Team retrospective at 7pm'],
        'confidence': 'high',
        'recommendation': 'Reschedule dinner to 8:30pm'
    }
    verdict = guardian_engine.evaluate('Book dinner reservation at 6:30pm', context)
    assert verdict.level == DisagreementLevel.CHALLENGE
    assert 'Gym workout at 6pm' in verdict.evidence
    assert verdict.recommendation == 'Reschedule dinner to 8:30pm'


def test_guardian_suggest_optimization():
    context = {
        'optimization_suggestion': 'Use Polars instead of Pandas for 10x faster CSV processing',
        'confidence': 'high'
    }
    verdict = guardian_engine.evaluate('Parse a 5GB CSV file in Python', context)
    assert verdict.level == DisagreementLevel.SUGGEST
    assert 'Polars' in verdict.reasoning


def test_guardian_format_challenge_level_2():
    verdict = GuardianVerdict(
        level=DisagreementLevel.CHALLENGE,
        reasoning="This violates your focus block schedule.",
        evidence=["Scheduled deep work from 2pm to 5pm"],
        confidence="high",
        recommendation="Move gaming to 6pm."
    )
    formatted = guardian_engine.format_challenge(verdict)
    assert "I disagree with this because" in formatted
    assert "Scheduled deep work" in formatted
    assert "Move gaming to 6pm" in formatted


def test_guardian_format_challenge_level_3():
    verdict = GuardianVerdict(
        level=DisagreementLevel.SAFETY,
        reasoning="This will wipe the primary disk.",
        requires_confirmation=True
    )
    formatted = guardian_engine.format_challenge(verdict)
    assert "explicit confirmation" in formatted


def test_guardian_verdict_to_dict():
    verdict = GuardianVerdict(
        level=DisagreementLevel.SAFETY,
        reasoning="Dangerous wipe",
        evidence=["drive D:"],
        confidence="high",
        recommendation="Do not wipe",
        requires_confirmation=True
    )
    d = verdict.to_dict()
    assert d['level'] == 3
    assert d['level_name'] == 'SAFETY'
    assert d['requires_confirmation'] is True
    assert d['reasoning'] == "Dangerous wipe"


def test_guardian_levels_enum_values():
    assert DisagreementLevel.EXECUTE.value == 0
    assert DisagreementLevel.SUGGEST.value == 1
    assert DisagreementLevel.CHALLENGE.value == 2
    assert DisagreementLevel.SAFETY.value == 3
