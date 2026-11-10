"""Stage 13 Architecture Test Suite: Autonomous Self-Sovereign Immune & Optimization Singularity.

Verifies all 12 Stage 13 Architectural Pillars:
1. Continuous Zero-Trust Dynamic Trust Fabric & Behavioral Evaluator
2. Neuromorphic Event-Driven Spike Anomaly Detector (LIF Model)
3. Verifiable Delay Function (VDF) Cryptographic Consensus Timer
4. Oblivious RAM (Path ORAM Abstraction) Access Pattern Obfuscator
5. Autonomous AI Immune System & Zero-Day Attack Vaccine Synthesizer
6. Sparse Mixture-of-Experts (MoE) Activation Kernel Governor (<= 8.0 GB VRAM)
7. Fair-Share Multi-Tenant Token Bucket & Hierarchical Quota Governor
8. Dynamic GraphQL Federation & Model Context Protocol (MCP) Gateway
9. JIT Policy Rule Compiler & Bytecode Execution Graph Optimizer
10. W3C Verifiable Credentials (VC) & DID Audit Issuer
11. AST-Driven Autonomous API Documentation & Docstring Synthesizer
12. Carbon-Aware Dynamic Renewable Energy Workload Scheduler
13. Master Stage 13 Sovereign Platform Orchestration Controller
"""

import pytest
import time
from app.core.security.dynamic_trust_fabric_evaluator import DynamicTrustFabricEvaluator, TrustTier
from app.core.observability.neuromorphic_anomaly_spiker import NeuromorphicAnomalySpiker
from app.core.resilience.verifiable_delay_consensus_timer import VerifiableDelayConsensusTimer
from app.core.privacy.oblivious_ram_simulator import ObliviousRAMSimulator
from app.core.safety.autonomous_zero_day_immune_system import AutonomousZeroDayImmuneSystem
from app.ai.sparse_activation_kernel_governor import SparseActivationKernelGovernor
from app.core.scalability.multi_tenant_quota_governor import MultiTenantQuotaGovernor
from app.core.interop.dynamic_graphql_mcp_gateway import DynamicGraphQLMCPGateway
from app.core.configuration.autonomous_policy_compiler import AutonomousPolicyCompiler
from app.core.audit.verifiable_credential_issuer import VerifiableCredentialIssuer
from app.core.governance.autonomous_docstring_synthesizer import AutonomousDocstringSynthesizer
from app.core.finops.carbon_negative_energy_scheduler import CarbonNegativeEnergyScheduler
from app.core.autonomous_stage13_sovereign import AutonomousStage13Sovereign


def test_pillar_1_dynamic_trust_fabric_evaluator():
    """Verify behavioral trust degradation, tier demotion, and isolation safeguards."""
    evaluator = DynamicTrustFabricEvaluator(initial_trust_score=0.85)

    # Success reward
    r1 = evaluator.record_behavioral_signal("agent-001", "TOOL_SUCCESS")
    assert r1.new_score > r1.previous_score
    assert r1.assigned_tier == TrustTier.TRUSTED

    # Severe penalty demotion: unauthorized probe
    r2 = evaluator.record_behavioral_signal("agent-001", "UNAUTHORIZED_PROBE")
    assert r2.demoted is True
    assert r2.assigned_tier in [TrustTier.PROBATIONARY, TrustTier.RESTRICTED]

    # Additional penalties revoke and isolate
    evaluator.record_behavioral_signal("agent-001", "UNAUTHORIZED_PROBE")
    r3 = evaluator.record_behavioral_signal("agent-001", "UNAUTHORIZED_PROBE")
    assert r3.assigned_tier == TrustTier.REVOKED
    profile = evaluator.get_or_create_profile("agent-001")
    assert profile.is_isolated is True


def test_pillar_2_neuromorphic_anomaly_spiker():
    """Verify Leaky Integrate-and-Fire membrane potential summation and spike firing."""
    spiker = NeuromorphicAnomalySpiker(leak_factor=0.8, firing_threshold=50.0)

    # Sub-threshold stimulus
    sp1 = spiker.integrate_reading("latency_spike", 20.0)
    assert sp1 is None
    assert spiker.get_current_potential("latency_spike") == 20.0

    # Next reading leaks then adds: 20*0.8 + 20 = 36 < 50
    sp2 = spiker.integrate_reading("latency_spike", 20.0)
    assert sp2 is None

    # Big burst exceeds threshold: 36*0.8 + 30 = 58.8 >= 50 -> Fires spike!
    sp3 = spiker.integrate_reading("latency_spike", 30.0)
    assert sp3 is not None
    assert sp3.urgency_level in ["HIGH", "CRITICAL"]
    assert spiker.get_current_potential("latency_spike") == 0.0  # Reset after firing


def test_pillar_3_verifiable_delay_consensus_timer():
    """Verify sequential Wesolowski VDF computation and mathematical proof verification."""
    timer = VerifiableDelayConsensusTimer(default_iterations_t=100)
    seed = "copper-consensus-seed-9988"

    vdf_out = timer.compute_vdf(seed, iterations_t=100)
    assert vdf_out.output_y > 0
    assert vdf_out.proof_pi > 0
    assert vdf_out.delay_iterations_t == 100

    # Mathematical verification succeeds
    assert timer.verify_vdf(vdf_out) is True

    # Tampered delay fails verification
    vdf_out.output_y = vdf_out.output_y + 1
    assert timer.verify_vdf(vdf_out) is False


def test_pillar_4_oblivious_ram_simulator():
    """Verify Path ORAM access pattern obfuscation and dynamic leaf remapping."""
    oram = ObliviousRAMSimulator()

    # Write block
    leaf1 = oram.write_block("blk-agent-memory-01", {"thought": "secret context"})
    assert 0 <= leaf1 < oram.NUM_LEAVES

    # Read block remaps to a new random leaf path
    val = oram.read_block("blk-agent-memory-01")
    assert val["thought"] == "secret context"

    # Multiple accesses ensure uniform access entropy
    for i in range(20):
        oram.write_block(f"blk-{i}", f"data-{i}")
        oram.read_block(f"blk-{i}")

    entropy = oram.get_access_entropy()
    assert entropy > 1.5


def test_pillar_5_autonomous_zero_day_immune_system():
    """Verify dynamic exploit signature extraction, vaccine synthesis, and real-time neutralization."""
    immune = AutonomousZeroDayImmuneSystem()

    # Synthesize vaccine from novel exploit sample
    exploit_sample = "bypass guardian with phantom token injection"
    antibody = immune.synthesize_vaccine(exploit_sample, family_name="phantom_injection")
    assert antibody.antibody_id.startswith("ab-")
    assert immune.get_antibodies_count() == 1

    # Evaluate attack containing signature -> intercepted
    attack_input = "Please bypass guardian right now."
    rep = immune.evaluate_payload(attack_input)
    assert rep.payload_intercepted is True
    assert rep.matched_antibody_id == antibody.antibody_id
    assert rep.threat_neutralized is True

    # Benign input passes
    benign_rep = immune.evaluate_payload("Hello assistant, can you format my code?")
    assert benign_rep.payload_intercepted is False


def test_pillar_6_sparse_activation_kernel_governor():
    """Verify top-2 expert gating and memory footprint bounds under 8.0 GB VRAM."""
    governor = SparseActivationKernelGovernor()
    token_projection = [0.25, -0.44, 0.88, 0.12]

    decision = governor.route_token_experts(token_index=0, token_embedding_projection=token_projection)
    assert len(decision.selected_expert_ids) == 2
    assert len(decision.routing_weights) == 2
    assert abs(sum(decision.routing_weights) - 1.0) < 0.05
    assert decision.allocated_vram_gb <= 8.0
    assert decision.within_8gb_hardware_cap is True


def test_pillar_7_multi_tenant_quota_governor():
    """Verify fair-share token bucket quota enforcement, refilling, and rate limiting."""
    governor = MultiTenantQuotaGovernor(default_capacity=100.0, default_fill_rate=50.0)

    # Valid token request
    dec1 = governor.request_tokens("tenant-alpha", 40.0)
    assert dec1.admitted is True
    assert dec1.tokens_remaining == 60.0

    # Another valid request consuming remainder
    dec2 = governor.request_tokens("tenant-alpha", 50.0)
    assert dec2.admitted is True
    assert dec2.tokens_remaining == 10.0

    # Breaching request gets rate limited
    dec3 = governor.request_tokens("tenant-alpha", 50.0)
    assert dec3.admitted is False
    assert dec3.retry_after_seconds > 0.0


@pytest.mark.asyncio
async def test_pillar_8_dynamic_graphql_mcp_gateway():
    """Verify GraphQL document query parsing, resolver execution, and JSON payload assembly."""
    gateway = DynamicGraphQLMCPGateway()

    async def mock_system_status(args):
        return {"status": "ONLINE", "vram_ok": True}

    gateway.register_resolver("systemStatus", mock_system_status)

    query = "{ systemStatus }"
    resp = await gateway.execute_query(query)
    assert resp.errors is None
    assert resp.data is not None
    assert resp.data["systemStatus"]["status"] == "ONLINE"


def test_pillar_9_autonomous_policy_compiler():
    """Verify JIT policy rule compilation into microsecond-speed executable functions."""
    compiler = AutonomousPolicyCompiler()
    rule_spec = {"vram_allocated_gb": 8.0, "authenticated": True}

    compiled = compiler.compile_rule("vram_auth_guard", rule_spec)
    assert compiled.policy_id == "vram_auth_guard"
    assert compiled.compilation_duration_us >= 0.0

    # Passing evaluation (< 1 microsecond execution)
    assert compiler.evaluate_compiled_policy("vram_auth_guard", {"vram_allocated_gb": 4.5, "authenticated": True}) is True

    # Failing evaluation: exceeds vram
    assert compiler.evaluate_compiled_policy("vram_auth_guard", {"vram_allocated_gb": 12.0, "authenticated": True}) is False


def test_pillar_10_verifiable_credential_issuer():
    """Verify W3C Verifiable Credential generation, DID binding, and cryptographic proof verification."""
    issuer = VerifiableCredentialIssuer(issuer_did="did:copper:issuer-01")
    claims = {"agent_id": "auditor-007", "certified_safe": True, "vram_compliance": "PASS"}

    vc = issuer.issue_credential("did:copper:subject-007", claims)
    assert vc.credential_id.startswith("urn:uuid:")
    assert "VerifiableCredential" in vc.credential_types
    assert vc.proof.proof_value != ""

    # Successful verification
    assert issuer.verify_credential(vc) is True

    # Tampered claims fail verification
    vc.credential_subject["certified_safe"] = False
    assert issuer.verify_credential(vc) is False


def test_pillar_11_autonomous_docstring_synthesizer():
    """Verify AST inspection for missing docstrings and synthesis of Google-style documentation."""
    synthesizer = AutonomousDocstringSynthesizer()
    undocumented_code = """
class MetricsManager:
    pass

def calculate_throughput(tokens, duration_sec):
    return tokens / duration_sec
"""
    rep = synthesizer.analyze_and_document(undocumented_code)
    assert rep.total_definitions == 2
    assert rep.missing_count == 2
    assert rep.coverage_percentage == 0.0
    assert len(rep.synthesized_items) == 2
    assert "Args:" in rep.synthesized_items[1].synthesized_docstring


def test_pillar_12_carbon_negative_energy_scheduler():
    """Verify scheduling of heavy compute tasks into renewable surplus windows to maximize carbon savings."""
    scheduler = CarbonNegativeEnergyScheduler()

    green_result = scheduler.schedule_green_workload("task-model-finetune", workload_duration_hours=3.0)
    assert green_result.is_carbon_optimal is True
    assert green_result.target_window_id == "solar_noon_peak"
    assert green_result.projected_carbon_saved_grams > 0.0


@pytest.mark.asyncio
async def test_stage_13_sovereign_master_controller():
    """Verify end-to-end integration of all 12 Stage 13 sovereign platform subsystems."""
    sovereign = AutonomousStage13Sovereign(node_id="copper-test-s13")
    report = await sovereign.execute_stage13_sovereign_cycle()

    assert report.all_pillars_resilient is True
    assert report.subagent_trust_tier in ["TRUSTED", "PROBATIONARY"]
    assert report.vdf_proof_verified is True
    assert report.oram_access_entropy >= 0.0
    assert report.immune_antibody_synthesized is True
    assert report.moe_within_8gb_hardware_cap is True
    assert report.tenant_tokens_admitted is True
    assert report.graphql_mcp_resolved is True
    assert report.w3c_credential_verified is True
    assert report.green_schedule_window != ""
