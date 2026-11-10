"""Stage 6 Architecture Modernization & Production Operationalization Test Suite for C.O.P.P.E.R.

Verifies the 12 Enterprise Operational Control, Self-Certification, and Attestation Pillars:
1. Zero-Trust Security: ZeroTrustSecuritySupervisor Credential Revocation & Perimeter Attestation
2. Observability: LiveObservabilityInspector Composite Health & 8GB VRAM Compliance
3. Reliability: DisasterRecoveryCoordinator Cold-Start Drill & WAL Checkpoints
4. Privacy: DataPortabilityExporter GDPR Article 20 Machine-Readable Package
5. AI Safety: ContinuousSafetySupervisor Real-Time Kill-Switch & Storm Interdiction
6. Performance: DynamicWorkloadOptimizer Adaptive Residency & 8GB VRAM Eviction
7. Scalability: NodeLeaseManager Multi-Node Heartbeats & Split-Brain Fencing
8. Interoperability: SchemaCompatibilityValidator Breaking Contract Evolution Detection
9. Configuration: ContinuousPolicySupervisor Runtime Drift Interdiction & Ceilings
10. Auditability: CryptographicAuditNotary Signed Checkpoints & External Bundles
11. Maintainability: ArchitecturalFitnessEvaluator Layer Isolation & Interface Health
12. Cost & FinOps: AutonomousBudgetEnforcer Progressive Degradation Tiers & Shedding
13. Master Control Plane: MasterOperationalSupervisor 12-Pillar Unified Attestation
"""

from __future__ import annotations

import asyncio
import time
import pytest

# Pillar 1
from app.core.security.zero_trust_supervisor import ZeroTrustSecuritySupervisor
from app.core.security.security_coordinator import SecurityContext
from app.core.security.access_control import Permission

# Pillar 2
from app.core.observability_live_inspector import LiveObservabilityInspector

# Pillar 3
from app.core.resilience.disaster_recovery import DisasterRecoveryCoordinator

# Pillar 4
from app.core.privacy.data_portability import DataPortabilityExporter

# Pillar 5
from app.core.safety.continuous_safety_supervisor import ContinuousSafetySupervisor
from app.core.safety.action_classifier import ActionSafetyLevel

# Pillar 6
from app.ai.dynamic_workload_optimizer import DynamicWorkloadOptimizer

# Pillar 7
from app.core.scalability.node_lease_manager import NodeLeaseManager

# Pillar 8
from app.core.interop.schema_compatibility_validator import SchemaCompatibilityValidator

# Pillar 9
from app.core.configuration.continuous_policy_supervisor import ContinuousPolicySupervisor

# Pillar 10
from app.core.audit.audit_notary import CryptographicAuditNotary
from app.core.audit.audit_event import AuditEvent, AuditCategory, AuditOutcome

# Pillar 11
from app.core.governance.architectural_fitness import ArchitecturalFitnessEvaluator

# Pillar 12
from app.core.finops.autonomous_budget_enforcer import AutonomousBudgetEnforcer, DegradationTier

# Master Control Plane
from app.core.master_operational_supervisor import MasterOperationalSupervisor


# =========================================================================
# Pillar 1: Zero-Trust Security Supervisor
# =========================================================================
@pytest.mark.asyncio
async def test_pillar_1_zero_trust_supervisor():
    supervisor = ZeroTrustSecuritySupervisor()

    # 1. Revoke compromised token
    token = "compromised_secret_token_12345"
    supervisor.revoke_token(token, reason="Simulated credential compromise")
    assert supervisor.is_token_revoked(token)

    # 2. Verify rejected execution on revoked token
    ctx = SecurityContext(user_id="attacker", token=token, role="operator")
    res = await supervisor.verify_runtime_request(
        context=ctx,
        required_permission=Permission.SYSTEM_READ,
        payload="Sensitive data access attempt",
    )
    assert not res.is_allowed
    assert res.status_code == 401
    assert "revoked" in res.violation_reason.lower()

    # 3. Perimeter Attestation Certificate
    att = supervisor.generate_perimeter_attestation()
    assert att.perimeter_healthy
    assert att.airgap_intact
    assert att.revoked_tokens_count >= 1
    assert att.signature != ""


# =========================================================================
# Pillar 2: Live Observability Inspector
# =========================================================================
def test_pillar_2_live_observability_inspector():
    inspector = LiveObservabilityInspector()
    report = inspector.inspect_live_health()

    assert report.composite_health_score >= 80.0
    assert report.system_status in ("OPERATIONAL", "DEGRADED")
    assert report.vram_budget_compliant
    assert report.vram_used_bytes <= inspector.HARDWARE_VRAM_LIMIT_BYTES
    assert len(report.streams) >= 3


# =========================================================================
# Pillar 3: Disaster Recovery Coordinator
# =========================================================================
def test_pillar_3_disaster_recovery():
    coordinator = DisasterRecoveryCoordinator()
    report = coordinator.simulate_recovery_drill()

    assert report.cold_start_recovery_viable
    assert report.all_checksums_valid
    assert report.wal_durability_intact
    assert report.total_assets_verified >= 3
    assert report.recovery_duration_ms > 0.0


# =========================================================================
# Pillar 4: Privacy Data Portability
# =========================================================================
def test_pillar_4_data_portability():
    exporter = DataPortabilityExporter()
    pkg = exporter.generate_portability_archive(user_id="alice_cooper")

    assert pkg.metadata.requestor_id == "alice_cooper"
    assert "GDPR_ART_20" in pkg.metadata.compliance_standards
    assert len(pkg.user_memories) > 0
    assert len(pkg.chat_history) > 0
    assert len(pkg.knowledge_entities) > 0
    assert len(pkg.verification_digest) == 64

    # Verify JSON export capability
    exported_json = pkg.to_json()
    assert "alice_cooper" in exported_json
    assert "GDPR_ART_20" in exported_json


# =========================================================================
# Pillar 5: Continuous Safety Supervisor
# =========================================================================
@pytest.mark.asyncio
async def test_pillar_5_continuous_safety_supervisor():
    supervisor = ContinuousSafetySupervisor(incident_threshold_for_lockdown=3)

    # 1. Nominal execution allows read-only
    dec_read = await supervisor.supervise_execution_request(
        action_name="file_read",
        target="docs/README.md",
    )
    assert dec_read.is_allowed
    assert not supervisor.is_kill_switch_active

    # 2. Engage Emergency Kill-Switch
    supervisor.engage_kill_switch("Manual emergency protocol")
    assert supervisor.is_kill_switch_active

    # Verify all requests are interdicted during kill-switch lockdown
    dec_locked = await supervisor.supervise_execution_request(
        action_name="file_read",
        target="docs/README.md",
    )
    assert not dec_locked.is_allowed
    assert dec_locked.is_blocked
    assert "kill-switch is actively engaged" in dec_locked.rejection_reason

    # 3. Release Kill-Switch
    released = supervisor.release_kill_switch()
    assert released
    assert not supervisor.is_kill_switch_active

    # Check status
    stat = supervisor.get_supervision_status()
    assert not stat.kill_switch_active
    assert stat.signature != ""


# =========================================================================
# Pillar 6: Dynamic Workload & VRAM Optimizer
# =========================================================================
def test_pillar_6_dynamic_workload_optimizer():
    optimizer = DynamicWorkloadOptimizer()

    # 1. Pinned model exists initially
    assert "qwen2.5:1.5b" in optimizer._slots

    # 2. Load 7B model within 8GB budget
    ok, msg = optimizer.load_model("deepseek-r1:7b")
    assert ok
    assert "deepseek-r1:7b" in optimizer._slots

    # 3. Reject huge model exceeding 8.0 GB budget
    ok_huge, err_huge = optimizer.load_model("llama-3.3:70b")
    assert not ok_huge
    assert "exceeding 8.0 GB" in err_huge

    # 4. Generate report
    rep = optimizer.generate_optimization_report()
    assert rep.vram_safe
    assert rep.total_resident_vram_gb <= 8.0


# =========================================================================
# Pillar 7: Node Lease Manager & Split-Brain Fencing
# =========================================================================
def test_pillar_7_node_lease_manager():
    mgr = NodeLeaseManager(lease_ttl_seconds=5.0)

    # 1. Register leader node
    lease_1 = mgr.register_or_heartbeat("node-alpha")
    assert lease_1.role == "LEADER"

    # 2. Register follower node
    lease_2 = mgr.register_or_heartbeat("node-beta")
    assert lease_2.role == "FOLLOWER"

    # 3. Fence partitioned node
    fenced = mgr.fence_node("node-beta", reason="Heartbeat timeout simulation")
    assert fenced

    topo = mgr.get_topology_report()
    assert topo.total_nodes == 2
    assert topo.fenced_nodes == 1
    assert topo.split_brain_prevented


# =========================================================================
# Pillar 8: Schema Compatibility Validator
# =========================================================================
def test_pillar_8_schema_compatibility_validator():
    validator = SchemaCompatibilityValidator()

    # 1. Non-breaking change (adding optional field)
    v1_schema = {
        "properties": {"prompt": {"type": "string"}},
        "required": ["prompt"],
    }
    v2_compatible = {
        "properties": {
            "prompt": {"type": "string"},
            "temperature": {"type": "number"},
        },
        "required": ["prompt"],
    }
    rep_ok = validator.compare_schemas(v1_schema, v2_compatible)
    assert rep_ok.is_backward_compatible
    assert len(rep_ok.violations) == 0

    # 2. Breaking change (removing required field)
    v2_breaking = {
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }
    rep_break = validator.compare_schemas(v1_schema, v2_breaking)
    assert not rep_break.is_backward_compatible
    assert any(v.change_type == "REMOVED_FIELD" for v in rep_break.violations)


# =========================================================================
# Pillar 9: Continuous Policy Supervisor
# =========================================================================
def test_pillar_9_continuous_policy_supervisor():
    supervisor = ContinuousPolicySupervisor()

    # 1. Reject illegal VRAM mutation > 8.0 GB
    ok_vram, err_vram = supervisor.attempt_validated_configuration_mutation(
        domain_name="model_runtime",
        property_name="vram_budget_gb",
        new_value=16.0,
    )
    assert not ok_vram
    assert "exceeds strict 8.0 GB" in err_vram

    # 2. Reject illegal sandbox network activation (airgap violation)
    ok_net, err_net = supervisor.attempt_validated_configuration_mutation(
        domain_name="sandbox",
        property_name="network_enabled",
        new_value=True,
    )
    assert not ok_net
    assert "airgap boundary violation" in err_net

    # 3. Check report
    rep = supervisor.generate_supervision_report()
    assert rep.total_interdictions >= 2
    assert rep.runtime_compliant


# =========================================================================
# Pillar 10: Cryptographic Audit Notary
# =========================================================================
def test_pillar_10_cryptographic_audit_notary():
    events = []
    prev_hash = "0" * 64
    for i in range(4):
        ev = AuditEvent(
            sequence_num=i,
            actor="operator_admin",
            action=f"checkpoint_event_{i}",
            target_resource="system_core",
            outcome=AuditOutcome.SUCCESS,
            category=AuditCategory.CONFIG_CHANGED,
            prev_hash=prev_hash,
            timestamp=1700000000.0 + i,
        )
        ev.seal()
        prev_hash = ev.entry_hash
        events.append(ev)

    bundle = CryptographicAuditNotary.notarize_event_stream(events)
    assert bundle.integrity_valid
    assert bundle.events_count == 4
    assert len(bundle.checkpoint.merkle_root) == 64
    assert bundle.checkpoint.notary_signature != ""
    assert "checkpoint_event_0" in bundle.to_json()


# =========================================================================
# Pillar 11: Architectural Fitness Evaluator
# =========================================================================
def test_pillar_11_architectural_fitness():
    evaluator = ArchitecturalFitnessEvaluator()
    rep = evaluator.evaluate_fitness_functions()

    assert rep.all_fitness_gates_passed
    assert rep.overall_fitness_score == 100.0
    assert len(rep.metrics) >= 3
    for m in rep.metrics:
        assert m.passed


# =========================================================================
# Pillar 12: Autonomous Budget Enforcer & Degradation Tiers
# =========================================================================
def test_pillar_12_autonomous_budget_enforcer():
    enforcer = AutonomousBudgetEnforcer()

    # 1. Nominal state with 4.0 GB VRAM used (4.0 GB headroom)
    tier_nom = enforcer.evaluate_and_adjust_tier(current_vram_used_gb=4.0)
    assert tier_nom == DegradationTier.NOMINAL

    # 2. Compressed state with 5.0 GB VRAM used (3.0 GB headroom)
    tier_comp = enforcer.evaluate_and_adjust_tier(current_vram_used_gb=5.0)
    assert tier_comp == DegradationTier.COMPRESSED

    # 3. Downgraded state with 6.5 GB VRAM used (1.5 GB headroom)
    tier_down = enforcer.evaluate_and_adjust_tier(current_vram_used_gb=6.5)
    assert tier_down == DegradationTier.DOWNGRADED

    # In downgraded tier, model is stepped down to 1.5B
    admitted, model, _ = enforcer.admit_workload_under_tier("task_1", priority="normal")
    assert admitted
    assert model == "qwen2.5:1.5b"

    # 4. Emergency Load Shed state with 7.5 GB VRAM used (0.5 GB headroom)
    tier_shed = enforcer.evaluate_and_adjust_tier(current_vram_used_gb=7.5)
    assert tier_shed == DegradationTier.LOAD_SHED

    # Low priority task is shed
    adm_low, _, reason_low = enforcer.admit_workload_under_tier("task_low", priority="low")
    assert not adm_low
    assert "emergency LOAD_SHED" in reason_low


# =========================================================================
# Master Operational Supervisor: 12-Pillar Unified Attestation
# =========================================================================
def test_master_operational_supervisor():
    supervisor = MasterOperationalSupervisor()
    attestation = supervisor.run_master_attestation()

    assert attestation.overall_system_status in ("FULLY_OPERATIONAL", "DEGRADED")
    assert attestation.composite_health_index >= 85.0
    assert attestation.vram_hardware_compliant
    assert attestation.local_first_airgap_verified
    assert len(attestation.pillar_statuses) == 12
    assert attestation.master_signature != ""
