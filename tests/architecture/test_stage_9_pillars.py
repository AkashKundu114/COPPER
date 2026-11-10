"""Stage 9 Architecture Test Suite: Autonomous Self-Healing & Distributed Resiliency.

Verifies all 12 Stage 9 Architectural Pillars:
1. Zero-Knowledge Attestation & Trustless Capability Verification
2. Cognitive Root Cause Analysis (RCA) & Causal Graphs
3. Byzantine Fault Tolerant (PBFT) Consensus & Replication
4. Partially Homomorphic & Additive Secure Evaluation
5. Cognitive Hallucination Reflector & Cross-Examiner
6. Zero-Downtime Live Model Migrator (<= 8.0 GB VRAM)
7. Adaptive Priority-Weighted Load Shedder (CoDel)
8. Distributed Local-First Event Mesh & Pub/Sub
9. Autonomous Configuration Drift Remediation
10. Verifiable Merkle Patricia Trie (MPT) State Ledger
11. Semantic Contract & Type Breaking Change Detector
12. Autonomous Multi-Tier Storage Lifecycle Balancer
13. Master Stage 9 Autonomous Orchestration Controller
"""

import pytest
import time
from app.core.security.zk_attestation_verifier import ZKAttestationVerifier
from app.core.observability.cognitive_root_cause_analyzer import CognitiveRootCauseAnalyzer, SymptomAlert
from app.core.resilience.byzantine_consensus_engine import ByzantineConsensusEngine, PBFTPhase
from app.core.privacy.homomorphic_evaluator import HomomorphicEvaluator
from app.core.safety.cognitive_hallucination_reflector import CognitiveHallucinationReflector
from app.ai.live_model_migrator import LiveModelMigrator
from app.core.scalability.adaptive_load_shedder import AdaptiveLoadShedder, WorkloadPriority
from app.core.interop.distributed_event_mesh import DistributedEventMesh, MeshEvent
from app.core.configuration.drift_remediation_orchestrator import DriftRemediationOrchestrator
from app.core.audit.verifiable_merkle_patricia_trie import VerifiableMerklePatriciaTrie
from app.core.governance.semantic_contract_diff_detector import SemanticContractDiffDetector, ContractChangeType
from app.core.finops.tier_storage_lifecycle_balancer import TierStorageLifecycleBalancer, StorageTier
from app.core.autonomous_stage9_orchestrator import AutonomousStage9Orchestrator


def test_pillar_1_zk_attestation_verifier():
    """Verify zero-knowledge commitment generation and trustless capability proof verification."""
    verifier = ZKAttestationVerifier()
    secret = "super-secret-capability-token-1234"
    verifier.register_capability_commitment("TOOL_EXECUTE_SENSITIVE", secret)

    proof = verifier.generate_attestation_proof("agent-tester", "TOOL_EXECUTE_SENSITIVE", secret, ttl_seconds=60)
    assert proof.proof_id.startswith("zk-prf-")
    assert not proof.is_expired
    assert verifier.verify_zk_proof(proof) is True

    # Tampered capability fails
    bad_proof = verifier.generate_attestation_proof("agent-tester", "SYSTEM_WRITE", secret, ttl_seconds=60)
    assert verifier.verify_zk_proof(bad_proof) is False


def test_pillar_2_cognitive_root_cause_analyzer():
    """Verify causal DAG traversal and Bayesian root cause posterior probability calculation."""
    analyzer = CognitiveRootCauseAnalyzer()
    alert = SymptomAlert(
        alert_id="alt-001",
        component_name="api_gateway",
        severity="HIGH",
        metric_name="p99_latency",
    )
    hypotheses = analyzer.analyze_root_cause([alert])
    assert len(hypotheses) >= 1
    # Check that root causes trace back to hardware/storage foundations
    root_components = [h.root_component for h in hypotheses]
    assert any(rc in ["gpu_vram", "disk_io", "inference_engine"] for rc in root_components)
    assert hypotheses[0].posterior_probability > 0.0
    assert hypotheses[0].remediation_suggestion != ""


def test_pillar_3_byzantine_consensus_engine():
    """Verify 3-phase PBFT consensus protocol under simulated quorum."""
    nodes = ["node-1", "node-2", "node-3", "node-4"]
    engine = ByzantineConsensusEngine(node_id="node-1", cluster_nodes=nodes)
    assert engine.f_max_faulty == 1
    assert engine.quorum_size == 3

    # Primary generates pre-prepare
    pre_prep = engine.create_pre_prepare(sequence_number=1, proposal_data={"ledger_entry": "tx-100"})
    assert pre_prep.phase == PBFTPhase.PRE_PREPARE

    # Execute full consensus round across quorum
    decision = engine.execute_full_consensus_round(sequence_number=1, proposal_data={"ledger_entry": "tx-100"})
    assert decision.sequence_number == 1
    assert decision.committed is True
    assert len(decision.commit_signatures) >= 3


def test_pillar_4_homomorphic_evaluator():
    """Verify additive homomorphic encryption and fixed-point scalar evaluation."""
    evaluator = HomomorphicEvaluator()
    v1 = 45.50
    v2 = 54.50

    c1 = evaluator.encrypt_scalar(v1)
    c2 = evaluator.encrypt_scalar(v2)

    # Perform addition over ciphertext: E(v1) * E(v2) mod n^2
    c_sum = evaluator.add_ciphertexts(c1, c2)

    # Decrypt and verify result
    result = evaluator.decrypt_scalar(c_sum)
    assert abs(result - 100.0) < 0.1


def test_pillar_5_cognitive_hallucination_reflector():
    """Verify hallucination detection for fabricated tools, URLs, and contextual groundedness."""
    reflector = CognitiveHallucinationReflector(registered_tools=["read_file", "write_file"])

    # Grounded response
    grounded_ctx = "COPPER uses local SQLite WAL for audit trails and configuration registries."
    grounded_resp = "The system logs audit trails using local SQLite WAL."
    g_res = reflector.evaluate_groundedness(grounded_resp, grounded_ctx)
    assert g_res.is_grounded is True
    assert g_res.grounding_score >= 0.35

    # Hallucinated response invoking non-existent tool
    hallucinated_resp = "I will execute call_tool('nuke_production_database') at http://phantom.fake.internal."
    h_res = reflector.evaluate_groundedness(hallucinated_resp, grounded_ctx)
    assert h_res.is_grounded is False
    assert len(h_res.detected_hallucinations) >= 1
    assert h_res.corrected_reflection is not None


def test_pillar_6_live_model_migrator():
    """Verify zero-downtime model hot-swapping and strict <= 8.0 GB VRAM boundary enforcement."""
    migrator = LiveModelMigrator(physical_vram_cap_gb=8.0)

    # Valid migration within budget
    desc = migrator.execute_live_migration(target_model="llama-3-8b-int4", target_vram_gb=5.5, active_kv_tokens=1024)
    assert desc.success is True
    assert desc.peak_transitional_vram_gb <= 8.0
    assert desc.kv_cache_tokens_transfused == 1024

    # Invalid migration exceeding physical hardware limit
    desc_over = migrator.execute_live_migration(target_model="llama-70b-fp16", target_vram_gb=140.0)
    assert desc_over.success is False
    assert desc_over.fallback_invoked is True


def test_pillar_7_adaptive_load_shedder():
    """Verify CoDel queue sojourn time evaluation and priority-based load shedding."""
    shedder = AdaptiveLoadShedder(target_sojourn_ms=50.0, max_queue_depth=10)

    # Enqueue standard and background tasks
    shedder.enqueue_task("task-bg-1", WorkloadPriority.BACKGROUND, {"type": "precache"})
    shedder.enqueue_task("task-vip-1", WorkloadPriority.CRITICAL_USER, {"type": "chat"})

    # Evaluate VIP task (should never shed)
    dec1 = shedder.evaluate_admission()
    assert dec1 is not None
    assert dec1.task_id == "task-bg-1"

    dec2 = shedder.evaluate_admission()
    assert dec2 is not None
    assert dec2.task_id == "task-vip-1"
    assert dec2.admitted is True


@pytest.mark.asyncio
async def test_pillar_8_distributed_event_mesh():
    """Verify decoupled asynchronous event pub/sub routing and delivery tracking."""
    mesh = DistributedEventMesh()
    delivered_events = []

    async def sample_subscriber(evt: MeshEvent) -> bool:
        delivered_events.append(evt.event_id)
        return True

    mesh.subscribe("copper.audit.event", sample_subscriber)

    evt = await mesh.publish_event(
        topic="copper.audit.event",
        partition_key="agent-01",
        payload={"action": "token_minted", "tokens": 150},
    )

    assert evt.event_id in delivered_events
    assert evt.acknowledged is True
    assert mesh.get_published_events_count() == 1


def test_pillar_9_drift_remediation_orchestrator():
    """Verify detection of configuration drift and autonomous state restoration."""
    orchestrator = DriftRemediationOrchestrator()

    # Inject unauthorized runtime drift
    orchestrator.set_runtime_override("model_runtime.max_vram_gb", 16.0)  # Violates 8.0 GB rule!
    orchestrator.set_runtime_override("security.zero_trust_strict", False)

    # Audit and auto-remediate
    report = orchestrator.audit_and_remediate(auto_reconcile=True)
    assert report.drifts_detected_count == 2
    assert report.remediations_applied_count == 2
    assert report.harmonized is True
    assert orchestrator.active_runtime_config["model_runtime.max_vram_gb"] == 8.0
    assert orchestrator.active_runtime_config["security.zero_trust_strict"] is True


def test_pillar_10_verifiable_merkle_patricia_trie():
    """Verify MPT authenticated key-value storage and cryptographic inclusion proof verification."""
    mpt = VerifiableMerklePatriciaTrie()
    root1 = mpt.put("accounts/alice/balance", 500)
    root2 = mpt.put("accounts/bob/balance", 300)

    assert root1 != root2
    assert mpt.get_root_hash() == root2

    # Generate and verify inclusion proof
    proof = mpt.generate_inclusion_proof("accounts/alice/balance")
    assert proof is not None
    assert proof.key == "accounts/alice/balance"
    assert mpt.verify_inclusion_proof(proof) is True


def test_pillar_11_semantic_contract_diff_detector():
    """Verify semantic breaking change detection in tool parameter schemas."""
    detector = SemanticContractDiffDetector()

    old_schema = {
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer"},
        },
        "required": ["query"],
    }

    # Compatible change: adding optional property
    compat_schema = {
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer"},
            "offset": {"type": "integer"},
        },
        "required": ["query"],
    }
    compat_rep = detector.compare_tool_schemas(old_schema, compat_schema)
    assert compat_rep.is_backward_compatible is True

    # Breaking change: removing property & adding required field
    breaking_schema = {
        "properties": {
            "search_term": {"type": "string"},
            "api_key": {"type": "string"},
        },
        "required": ["search_term", "api_key"],
    }
    breaking_rep = detector.compare_tool_schemas(old_schema, breaking_schema)
    assert breaking_rep.is_backward_compatible is False
    assert breaking_rep.breaking_changes_count >= 2


def test_pillar_12_tier_storage_lifecycle_balancer():
    """Verify hierarchical storage tiering and idle cache demotion."""
    balancer = TierStorageLifecycleBalancer()

    # Store artifact in VRAM
    art = balancer.store_artifact("kv-cache-sess-1", size_mb=128.0, tier=StorageTier.VRAM)
    assert art.current_tier == StorageTier.VRAM
    assert balancer.get_tier_usage_mb(StorageTier.VRAM) == 128.0

    # Simulate artifact aging (idle for 120s)
    art.last_accessed = time.time() - 120.0
    actions = balancer.rebalance_tiers()

    assert len(actions) == 1
    assert actions[0].from_tier == StorageTier.VRAM
    assert actions[0].to_tier == StorageTier.RAM
    assert balancer.get_tier_usage_mb(StorageTier.VRAM) == 0.0
    assert balancer.get_tier_usage_mb(StorageTier.RAM) == 128.0


@pytest.mark.asyncio
async def test_stage_9_master_orchestrator():
    """Verify end-to-end orchestration of all 12 Stage 9 autonomous subsystems."""
    orch = AutonomousStage9Orchestrator(node_id="copper-test-s9")
    report = await orch.execute_stage9_orchestration_cycle()

    assert report.all_pillars_resilient is True
    assert report.zk_proof_valid is True
    assert report.pbft_quorum_consensus_reached is True
    assert report.homomorphic_computation_verified is True
    assert report.hallucination_reflection_passed is True
    assert report.vram_within_8gb_hardware_cap is True
    assert report.vram_peak_transitional_gb <= 8.0
    assert report.load_shedder_tasks_admitted >= 1
    assert report.event_mesh_published_count >= 1
    assert report.config_drift_harmonized is True
    assert report.semantic_contract_compatible is True
