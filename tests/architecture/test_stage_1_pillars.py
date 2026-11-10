"""Automated Verification Suite for Stage 1 Architectural Deliverables.

Validates:
  1. AI Safety & Alignment (Policy Engine & Invariants)
  2. Performance & Optimization (Quantization-Aware VRAM Estimator)
  3. Scalability (Deployment Profiles)
  4. Interoperability & Integration (Error Envelope & Agent Contract)
  5. Configuration Management (Modular Domain Schemas)
  6. Auditability & Accountability (Cryptographic Hash Chaining)
  7. Maintainability & Evolvability (Runtime Protocols & ADRs)
  8. Cost & Resource Governance (FinOps Resource Accounting Ledger)
"""

from __future__ import annotations

from pathlib import Path
import pytest

# 1. AI Safety
from app.core.safety.policy_engine import (
    PolicyLevel,
    SafetyPolicyEngine,
    SafetyRule,
)

# 2. Performance & Optimization
from app.ai.llm.quantization_vram import (
    QuantizationType,
    quantization_vram_estimator,
)

# 3. Scalability
from app.core.scalability.profiles import (
    DeploymentProfile,
    ProfileManager,
    SessionStorageBackend,
)

# 4. Interoperability & Integration
from app.core.interop.agent_contract import (
    AgentMetadata,
    AgentRequest,
    AgentResponse,
    ResponseStatus,
)
from app.core.interop.errors import (
    COPPERErrorResponse,
    ErrorCode,
)

# 5. Configuration Management
from app.core.configuration.schemas import (
    AppIdentityConfig,
    COPPERConfig,
    DatabaseConfig,
    ModelRuntimeConfig,
)

# 6. Auditability & Accountability
from app.core.audit.audit_event import (
    AuditCategory,
    AuditEvent,
    AuditOutcome,
    GENESIS_HASH,
)

# 7. Maintainability & Protocols
from app.core.interfaces.runtime_protocols import (
    ModelRuntimeProtocol,
    StorageAdapterProtocol,
)

# 8. FinOps Ledger
from app.core.finops.ledger import (
    ResourceAccountingLedger,
    ResourceUsageRecord,
)


# ==============================================================================
# 1. AI Safety & Alignment Tests
# ==============================================================================
def test_safety_policy_engine_invariants():
    engine = SafetyPolicyEngine()
    # Check that hard invariants cannot be overridden by lower priority
    lower_rule = SafetyRule(
        rule_id="INV-001",
        name="AttemptedOverride",
        description="Try to weaken invariant",
        level=PolicyLevel.AGENT_HEURISTIC,
        action_type="file_system",
        condition="rm -rf /",
        is_blocked=False,
    )
    success, msg = engine.register_rule(lower_rule)
    assert success is False
    assert "Cannot override System Invariant" in msg

    # Verify action evaluation
    permitted, conf, reason = engine.evaluate_action("file_system", "format c: /fs:NTFS")
    assert permitted is False
    assert "Blocked by SYSTEM_INVARIANT" in reason


# ==============================================================================
# 2. Performance & Quantization VRAM Tests
# ==============================================================================
def test_quantization_vram_estimation():
    footprint_14b_q4 = quantization_vram_estimator.estimate_vram("qwen2.5:14b-q4_k_m")
    assert footprint_14b_q4.quantization == QuantizationType.Q4_K_M
    assert footprint_14b_q4.fits_8gb_vram is True
    assert 6.0 <= footprint_14b_q4.total_vram_gb <= 7.5

    footprint_14b_fp16 = quantization_vram_estimator.estimate_vram("qwen2.5:14b-fp16")
    assert footprint_14b_fp16.quantization == QuantizationType.FP16
    assert footprint_14b_fp16.fits_8gb_vram is False  # 14B FP16 exceeds 8GB VRAM


# ==============================================================================
# 3. Scalability Deployment Profiles Tests
# ==============================================================================
def test_deployment_profiles():
    mgr = ProfileManager()
    mgr.set_profile(DeploymentProfile.DESKTOP)
    spec = mgr.current_spec
    assert spec.profile == DeploymentProfile.DESKTOP
    assert spec.session_backend == SessionStorageBackend.LOCAL_JSON
    assert spec.enable_distributed_locking is False

    mgr.set_profile(DeploymentProfile.CLUSTER)
    spec_cluster = mgr.current_spec
    assert spec_cluster.enable_distributed_locking is True
    assert spec_cluster.enable_hpa is True


# ==============================================================================
# 4. Interoperability & Error Envelope Tests
# ==============================================================================
def test_interop_contract_and_error_envelope():
    err = COPPERErrorResponse(
        error_code=ErrorCode.PERMISSION_DENIED,
        message="Agent unprivileged for tool",
        status_code=403,
        retryable=False,
    )
    err_dict = err.to_dict()
    assert err_dict["error_code"] == "PERMISSION_DENIED"
    assert err_dict["status_code"] == 403

    req = AgentRequest(task="Refactor sorting function", caller="user")
    assert req.caller == "user"

    meta = AgentMetadata(agent_id="VULCAN", model_name="qwen2.5-coder:14b", latency_ms=120.5)
    res = AgentResponse(
        request_id=req.request_id,
        status=ResponseStatus.SUCCESS,
        content="Refactored code.",
        metadata=meta,
    )
    res_dict = res.to_dict()
    assert res_dict["status"] == "SUCCESS"
    assert res_dict["metadata"]["agent_id"] == "VULCAN"


# ==============================================================================
# 5. Configuration Management Schemas Tests
# ==============================================================================
def test_configuration_domain_schemas():
    cfg = COPPERConfig(
        identity=AppIdentityConfig(app_version="3.0.0"),
        database=DatabaseConfig(pool_size=15),
        model_runtime=ModelRuntimeConfig(vram_budget_gb=8.0),
    )
    assert cfg.identity.app_version == "3.0.0"
    assert cfg.database.pool_size == 15
    assert cfg.model_runtime.vram_budget_gb == 8.0


# ==============================================================================
# 6. Auditability & Hash Chaining Tests
# ==============================================================================
def test_audit_hash_chaining():
    genesis = AuditEvent.create_genesis()
    assert genesis.prev_hash == GENESIS_HASH
    assert len(genesis.entry_hash) == 64

    event_1 = AuditEvent(
        sequence_num=1,
        category=AuditCategory.TOOL_EXECUTED,
        actor="VULCAN",
        action="shell_execute",
        target_resource="tool:shell_execute",
        outcome=AuditOutcome.SUCCESS,
        prev_hash=genesis.entry_hash,
    )
    event_1.seal()
    assert event_1.prev_hash == genesis.entry_hash
    assert len(event_1.entry_hash) == 64
    assert event_1.entry_hash != genesis.entry_hash


# ==============================================================================
# 7. Maintainability Protocols & ADR Tests
# ==============================================================================
def test_runtime_protocols_and_adr_presence():
    adr_file = Path("docs/adr/ADR-0001_LOCAL_FIRST_8GB_VRAM.md")
    assert adr_file.exists(), "Foundational ADR-0001 must exist on disk"
    assert "8GB VRAM" in adr_file.read_text(encoding="utf-8")

    class DummyStorage:
        async def get(self, key: str):
            return "value"
        async def put(self, key: str, value, ttl_seconds=None):
            return True
        async def delete(self, key: str):
            return True
        async def exists(self, key: str):
            return True

    dummy = DummyStorage()
    assert isinstance(dummy, StorageAdapterProtocol)


# ==============================================================================
# 8. FinOps Resource Accounting Ledger Tests
# ==============================================================================
def test_finops_resource_accounting_ledger():
    ledger = ResourceAccountingLedger()
    record = ResourceUsageRecord(
        task_id="task_1001",
        agent_id="VULCAN",
        model_name="qwen2.5-coder:14b",
        cpu_time_ms=45.2,
        inference_duration_ms=620.0,
        prompt_tokens=150,
        completion_tokens=220,
        total_tokens=370,
        cost_usd=0.0,
    )
    ledger.record_usage(record)

    summary = ledger.get_agent_summary("VULCAN")
    assert summary["total_tokens"] == 370.0
    assert summary["invocation_count"] == 1.0

    global_sum = ledger.get_global_summary()
    assert global_sum["total_tokens"] == 370.0
    assert "VULCAN" in global_sum["tracked_agents"]
