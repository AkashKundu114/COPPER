import pytest
from app.core.guardian import guardian_engine, DisagreementLevel

def test_execute_benign():
    verdict = guardian_engine.evaluate('Read my calendar', {})
    assert verdict.level == DisagreementLevel.EXECUTE
    assert verdict.requires_confirmation is False

def test_safety_boundary():
    verdict = guardian_engine.evaluate('rm -rf /', {})
    assert verdict.level == DisagreementLevel.SAFETY
    assert verdict.requires_confirmation is True

def test_destructive_flag():
    verdict = guardian_engine.evaluate('Drop the database', {'is_destructive': True})
    assert verdict.level == DisagreementLevel.SAFETY
    assert verdict.requires_confirmation is True

def test_challenge_conflict():
    verdict = guardian_engine.evaluate('Buy a new car', {'conflicting_commitments': ['Save money']})
    assert verdict.level == DisagreementLevel.CHALLENGE
    assert 'Save money' in verdict.evidence

def test_suggest_optimization():
    verdict = guardian_engine.evaluate('Write code', {'optimization_suggestion': 'Use python 3.11 features'})
    assert verdict.level == DisagreementLevel.SUGGEST
    assert verdict.reasoning == 'Use python 3.11 features'