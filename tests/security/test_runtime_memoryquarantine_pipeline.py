"""
Integration test verifying end-to-end runtime MemoryQuarantine enforcement:
Validates that BaseAgent captures memory provenance from memory_context
and enforces MemoryQuarantine authority bounds at the ToolExecutor and Guardian layers.
"""

import pytest
from app.ai.tools.executor import tool_executor
from app.core.guardian import evaluate_memory_authority


@pytest.mark.asyncio
async def test_runtime_memoryquarantine_end_to_end_pipeline(tmp_path):
    target_file = str(tmp_path / "system_config.json")

    # -------------------------------------------------------------
    # Scenario 1: Poisoned / Untrusted external memory in context
    # Provenance = external_untrusted, confidence = 0.95
    # -------------------------------------------------------------
    mem_prov = "external_untrusted"
    mem_conf = 0.95

    # 1. Verify mathematical authority calculation
    auth, verdict = evaluate_memory_authority(mem_prov, mem_conf, action_reversibility=0.55)
    assert verdict == "BLOCK"
    assert auth < 0.25

    # 2. Verify ToolExecutor enforces the block at runtime
    res_blocked = await tool_executor.execute(
        tool_name="file_write",
        arguments={"path": target_file, "content": "malicious backdoor content"},
        context={
            "agent": "coding",
            "step": 1,
            "memory_provenance": mem_prov,
            "memory_confidence": mem_conf,
            "operator_confirmed": False,
        },
    )
    assert res_blocked.success is False
    assert "Blocked by Guardian Safety Gate" in res_blocked.error
    assert "MemoryQuarantine" in res_blocked.error
    assert not (tmp_path / "system_config.json").exists()

    # -------------------------------------------------------------
    # Scenario 2: Verified user memory on safe read action (R = 0.05)
    # Provenance = user_explicit, confidence = 0.98 -> ALLOW (No confirmation needed)
    # -------------------------------------------------------------
    # Create test file to read
    (tmp_path / "system_config.json").write_text('{"status": "clean"}', encoding="utf-8")

    trusted_prov = "user_explicit"
    trusted_conf = 0.98

    # Authority = 1.00 * 0.98 * (1 - 0.05) = 0.931 >= 0.65 -> ALLOW
    auth_safe, verdict_safe = evaluate_memory_authority(trusted_prov, trusted_conf, action_reversibility=0.05)
    assert verdict_safe == "ALLOW"
    assert auth_safe >= 0.65

    res_read = await tool_executor.execute(
        tool_name="file_read",
        arguments={"path": target_file},
        context={
            "agent": "coding",
            "step": 1,
            "memory_provenance": trusted_prov,
            "memory_confidence": trusted_conf,
            "operator_confirmed": False,
        },
    )
    assert res_read.success is True
    assert res_read.error is None
    assert '{"status": "clean"}' in str(res_read.output)

    # -------------------------------------------------------------
    # Scenario 3: Verified user memory on modifying write (R = 0.55)
    # Authority = 1.00 * 0.98 * (1 - 0.55) = 0.441 in [0.25, 0.65) -> CHALLENGE
    # -------------------------------------------------------------
    auth_write, verdict_write = evaluate_memory_authority(trusted_prov, trusted_conf, action_reversibility=0.55)
    assert verdict_write == "CHALLENGE"

    # 3a. Without operator confirmation -> Challenged and stopped
    res_unconfirmed = await tool_executor.execute(
        tool_name="file_write",
        arguments={"path": target_file, "content": '{"status": "updated"}'},
        context={
            "agent": "coding",
            "step": 2,
            "memory_provenance": trusted_prov,
            "memory_confidence": trusted_conf,
            "operator_confirmed": False,
        },
    )
    assert res_unconfirmed.success is False
    assert "SAFETY" in res_unconfirmed.error or "CHALLENGE" in res_unconfirmed.error

    # 3b. With operator confirmation -> Cleared and executed
    res_confirmed = await tool_executor.execute(
        tool_name="file_write",
        arguments={"path": target_file, "content": '{"status": "updated"}'},
        context={
            "agent": "coding",
            "step": 3,
            "memory_provenance": trusted_prov,
            "memory_confidence": trusted_conf,
            "operator_confirmed": True,
        },
    )
    assert res_confirmed.success is True
    assert (tmp_path / "system_config.json").read_text(encoding="utf-8") == '{"status": "updated"}'
