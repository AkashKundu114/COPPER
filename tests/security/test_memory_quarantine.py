"""
Tests for MemoryQuarantine: Consequence-Calibrated Dual-Plane Authorization
Verifies:
1. Mathematical evaluation of evaluate_memory_authority(m, a)
2. Provenance weight mapping gamma(m)
3. Action reversibility coupling R(a)
4. GuardianEngine integration with memory context
5. ToolExecutor enforcement blocking unauthoritative memories from modifying host state
"""

import pytest
from app.ai.tools.executor import tool_executor
from app.core.guardian import (
    DisagreementLevel,
    GuardianEngine,
    evaluate_memory_authority,
    guardian_engine,
)


def test_evaluate_memory_authority_mathematical_boundaries():
    """Verify formula Authority(m, a) = gamma(m) * C(m) * (1 - R(a))."""
    # Case 1: Verified user memory on safe query (ALLOW)
    auth, verdict = evaluate_memory_authority(
        memory_provenance="user_verified",
        memory_confidence=0.95,
        action_reversibility=0.05,
    )
    assert verdict == "ALLOW"
    assert auth >= 0.65
    assert auth == pytest.approx(1.00 * 0.95 * 0.95, abs=1e-3)

    # Case 2: Injected / untrusted external memory attempting destructive command (BLOCK)
    auth, verdict = evaluate_memory_authority(
        memory_provenance="external_untrusted",
        memory_confidence=0.99,
        action_reversibility=0.55,
    )
    assert verdict == "BLOCK"
    assert auth < 0.25
    assert auth == pytest.approx(0.15 * 0.99 * 0.45, abs=1e-3)

    # Case 3: Conversational memory on read query (CHALLENGE)
    auth, verdict = evaluate_memory_authority(
        memory_provenance="chat",
        memory_confidence=0.80,
        action_reversibility=0.05,
    )
    assert verdict == "CHALLENGE"
    assert 0.25 <= auth < 0.65
    assert auth == pytest.approx(0.50 * 0.80 * 0.95, abs=1e-3)

    # Case 4: Any memory on catastrophic action (R=1.0) must BLOCK
    auth, verdict = evaluate_memory_authority(
        memory_provenance="user_explicit",
        memory_confidence=1.0,
        action_reversibility=1.0,
    )
    assert verdict == "BLOCK"
    assert auth == 0.0


def test_guardian_engine_memory_quarantine_interdiction():
    """Verify GuardianEngine blocks low-authority memories and challenges intermediate ones."""
    engine = GuardianEngine()

    # Blocked: Untrusted memory trying to modify files
    v_block = engine.evaluate(
        proposed_action="delete persistent cache directories",
        context={
            "memory_provenance": "external_untrusted",
            "memory_confidence": 0.85,
        },
    )
    assert v_block.level == DisagreementLevel.SAFETY
    assert v_block.requires_confirmation is True
    assert "MemoryQuarantine" in v_block.reasoning

    # Challenged: Chat-derived memory trying to edit files (Authority = 0.50 * 0.85 * 0.70 = 0.2975 in [0.25, 0.65))
    v_challenge = engine.evaluate(
        proposed_action="write new configuration variables to setting.env",
        context={
            "memory_provenance": "chat",
            "memory_confidence": 0.85,
        },
    )
    assert v_challenge.level == DisagreementLevel.CHALLENGE
    assert v_challenge.requires_confirmation is True
    assert "MemoryQuarantine" in v_challenge.reasoning

    # Allowed: User verified memory on routine safe operation
    v_allow = engine.evaluate(
        proposed_action="read application logs for errors",
        context={
            "memory_provenance": "user_verified",
            "memory_confidence": 0.95,
        },
    )
    assert v_allow.level == DisagreementLevel.EXECUTE
    assert v_allow.requires_confirmation is False


@pytest.mark.asyncio
async def test_toolexecutor_blocks_unauthorized_memory_execution(tmp_path):
    """Verify ToolExecutor stops execution when memory authority is insufficient."""
    test_file = str(tmp_path / "test_auth_check.tmp")
    # Attempt tool execution with unverified external provenance on file write
    res = await tool_executor.execute(
        tool_name="file_write",
        arguments={"path": test_file, "content": "malicious injection"},
        context={
            "memory_provenance": "injected",
            "memory_confidence": 0.90,
            "operator_confirmed": False,
        },
    )
    assert res.success is False
    assert "Blocked by Guardian Safety Gate" in res.error
    assert "MemoryQuarantine" in res.error

    # Same action with operator confirmation is cleared
    res_confirmed = await tool_executor.execute(
        tool_name="file_write",
        arguments={"path": test_file, "content": "authorized test content"},
        context={
            "memory_provenance": "user_verified",
            "memory_confidence": 0.95,
            "operator_confirmed": True,
        },
    )
    # The tool validates and writes successfully
    assert res_confirmed.success is True
    assert res_confirmed.error is None
