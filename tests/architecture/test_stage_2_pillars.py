"""Automated Verification Suite for Stage 2 Architectural Deliverables.

Validates:
  1. AI Safety & Alignment (4-Tier Action Classifier & Escalation Ticketing)
  2. Performance & Optimization (Context Optimizer & Token Budgeting)
  3. Scalability (Distributed Lock Manager & Hybrid Leasing)
  4. Interoperability & Integration (Tool Execution Contract Wrapper)
  5. Configuration Management (Dynamic Config Change & Rollback Manager)
  6. Auditability & Accountability (Audit Service & Chain Integrity Verifier)
  7. Maintainability & Evolvability (ADRs 0001-0006 & Boundary Linter)
  8. Cost & Resource Governance (Budget Registry & Workload Admission Controller)
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import pytest

# 1. AI Safety Stage 2
from app.core.safety.action_classifier import (
    ActionSafetyClassifier,
    ActionSafetyLevel,
)
from app.core.safety.escalation import (
    SafetyEscalationManager,
    TicketStatus,
)

# 2. Performance Stage 2
from app.ai.memory.context_optimizer import (
    ContextOptimizer,
)

# 3. Scalability Stage 2
from app.core.scalability.distributed_lock import (
    DistributedLockManager,
)

# 4. Interoperability Stage 2
from app.ai.tools.registry import BaseTool
from app.core.interop.tool_contract import (
    ToolContractWrapper,
)

# 5. Configuration Stage 2
from app.core.configuration.change_manager import (
    ConfigChangeManager,
)
from app.core.configuration.schemas import (
    COPPERConfig,
)

# 6. Auditability Stage 2
from app.core.audit.audit_event import (
    AuditCategory,
    AuditOutcome,
)
from app.core.audit.audit_service import (
    AuditService,
)
from app.core.audit.verifier import (
    AuditIntegrityVerifier,
)

# 7. FinOps Stage 2
from app.core.finops.admission_controller import (
    ResourceAdmissionController,
)
from app.core.finops.budgets import (
    ResourceBudgetRegistry,
)


# ==============================================================================
# 1. AI Safety Stage 2 Tests
# ==============================================================================
def test_action_safety_classifier_and_escalation():
    classifier = ActionSafetyClassifier()

    # Read-only tool
    res_read = classifier.classify_tool_call("file_read", {"path": "test.txt"})
    assert res_read.level == ActionSafetyLevel.READ_ONLY
    assert res_read.requires_approval is False

    # Consequential tool
    res_write = classifier.classify_tool_call("file_write", {"path": "main.py", "content": "..."})
    assert res_write.level == ActionSafetyLevel.CONSEQUENTIAL
    assert res_write.requires_approval is True

    # Irreversible destructive command
    res_wipe = classifier.classify_tool_call("shell_execute", {"command": "rm -rf /"})
    assert res_wipe.level == ActionSafetyLevel.IRREVERSIBLE
    assert res_wipe.is_blocked is True

    # Escalation manager ticketing
    esc_mgr = SafetyEscalationManager()
    ticket = esc_mgr.create_ticket("file_write", "file_write(path='main.py')", "Consequential write")
    assert ticket.status == TicketStatus.PENDING
    assert ticket.is_valid_approval() is False

    esc_mgr.approve_ticket(ticket.ticket_id, "Operator approved")
    assert ticket.status == TicketStatus.APPROVED
    assert ticket.is_valid_approval() is True


# ==============================================================================
# 2. Performance Stage 2 Tests
# ==============================================================================
def test_context_optimizer_deduplication_and_budget():
    optimizer = ContextOptimizer(default_token_budget=50)

    facts = [
        "- User name is Akash Kundu",
        "- [MEMORY id=mem_1]: User name is Akash Kundu",  # Near duplicate
        "- Role is Software Engineer",
        "- Hardware is RTX 5060 Laptop GPU",
        "- Irrelevant long fact that should be pruned if exceeding budget 1234567890",
    ]

    res = optimizer.optimize_context(facts, token_budget=20)
    assert res.duplicates_removed >= 1
    assert res.optimized_estimated_tokens <= 20
    assert "Akash Kundu" in res.optimized_text


# ==============================================================================
# 3. Scalability Stage 2 Tests
# ==============================================================================
@pytest.mark.asyncio
async def test_distributed_lock_manager_leasing():
    lock_mgr = DistributedLockManager(default_lease_seconds=2)
    resource = "test_dag_123"

    # Acquire lock
    lock1 = await lock_mgr.acquire_lock(resource, lease_seconds=2, timeout_seconds=1.0)
    assert lock1 is not None

    # Competing acquire must fail within timeout
    lock2 = await lock_mgr.acquire_lock(resource, lease_seconds=2, timeout_seconds=0.1)
    assert lock2 is None

    # Release lock1
    released = await lock1.release()
    assert released is True

    # Now lock2 can acquire
    lock3 = await lock_mgr.acquire_lock(resource, lease_seconds=2, timeout_seconds=0.5)
    assert lock3 is not None
    await lock3.release()


# ==============================================================================
# 4. Interoperability Stage 2 Tests
# ==============================================================================
@pytest.mark.asyncio
async def test_tool_contract_wrapper_execution():
    wrapper = ToolContractWrapper(default_timeout_seconds=2.0)

    async def sample_tool_fn(x: int) -> int:
        return x * 2

    tool = BaseTool(
        name="multiplier",
        description="Multiplies by 2",
        parameters={"properties": {"x": {"type": "integer"}}, "required": ["x"]},
        func=sample_tool_fn,
    )

    # Valid execution
    res = await wrapper.execute_contract(tool, {"x": 5})
    assert res.success is True
    assert res.output == 10

    # Idempotent execution (from cache)
    res_cached = await wrapper.execute_contract(tool, {"x": 5})
    assert res_cached.success is True
    assert res_cached.idempotent_cached is True

    # Validation failure
    res_bad = await wrapper.execute_contract(tool, {"x": "not_an_int"})
    assert res_bad.success is False
    assert res_bad.error.status_code == 400

    # Timeout tool
    async def slow_fn():
        await asyncio.sleep(2.0)
        return "done"

    slow_tool = BaseTool(
        name="slow_tool",
        description="Slow operation",
        parameters={},
        func=slow_fn,
    )
    res_timeout = await wrapper.execute_contract(slow_tool, {}, timeout_seconds=0.1)
    assert res_timeout.success is False
    assert res_timeout.error.error_code == "TIMEOUT"


# ==============================================================================
# 5. Configuration Stage 2 Tests
# ==============================================================================
def test_config_change_manager_and_rollback():
    cfg = COPPERConfig()
    mgr = ConfigChangeManager(cfg)

    # Valid update
    ok, msg = mgr.update_property("model_runtime", "vram_budget_gb", 12.0, operator="admin")
    assert ok is True
    assert mgr.config.model_runtime.vram_budget_gb == 12.0

    # Invalid update (violating Pydantic ge=2.0, le=48.0)
    bad_ok, bad_msg = mgr.update_property("model_runtime", "vram_budget_gb", 100.0, operator="admin")
    assert bad_ok is False
    assert "Validation failed" in bad_msg

    # Rollback
    rb_ok, rb_msg = mgr.rollback()
    assert rb_ok is True
    assert mgr.config.model_runtime.vram_budget_gb == 8.0  # restored to default!


# ==============================================================================
# 6. Auditability Stage 2 Tests
# ==============================================================================
@pytest.mark.asyncio
async def test_audit_service_and_verifier():
    service = AuditService()

    # Log 3 chained events
    ev1 = await service.log_event(
        category=AuditCategory.AUTH_LOGIN,
        actor="operator",
        action="user_login",
        target_resource="session_1",
        outcome=AuditOutcome.SUCCESS,
    )
    ev2 = await service.log_event(
        category=AuditCategory.TOOL_EXECUTED,
        actor="VULCAN",
        action="file_read",
        target_resource="tool:file_read",
        outcome=AuditOutcome.SUCCESS,
    )

    # Verify intact chain
    ver_res = service.verify_integrity()
    assert ver_res.is_valid is True
    assert ver_res.verified_events_count >= 3  # Genesis + 2 events

    # Simulate tampering on event 1 payload
    ev1.action = "tampered_action"
    tampered_res = AuditIntegrityVerifier.verify_chain(service._events)
    assert tampered_res.is_valid is False
    assert "tampering detected" in tampered_res.error_message.lower()


# ==============================================================================
# 7. Maintainability Stage 2 Tests
# ==============================================================================
def test_adr_suite_and_boundary_linter():
    # Check all ADRs 0001 through 0006 exist
    for num in ["0001", "0002", "0003", "0004", "0005", "0006"]:
        matched = list(Path("docs/adr").glob(f"ADR-{num}_*.md"))
        assert len(matched) == 1, f"Missing ADR-{num} in docs/adr/"

    # Run boundary linter function
    from scripts.lint_architecture import lint_all_architecture
    assert lint_all_architecture() == 0, "Architectural boundary linter must find 0 violations"


# ==============================================================================
# 8. FinOps Stage 2 Tests
# ==============================================================================
def test_budget_registry_and_admission_controller():
    registry = ResourceBudgetRegistry()
    controller = ResourceAdmissionController(budget_registry=registry)

    # Normal admission
    verd = controller.evaluate_task_admission("task_1", "CODING", priority=1, estimated_tokens=1000)
    assert verd.admitted is True

    # Exhaust agent budget
    coding_b = registry.get_agent_budget("CODING")
    coding_b.record_tokens(150000)  # Exceeds 100,000 hourly quota

    verd_exhausted = controller.evaluate_task_admission("task_2", "CODING", priority=1, estimated_tokens=1000)
    assert verd_exhausted.admitted is False
    assert "budget exceeded" in verd_exhausted.reason.lower()
