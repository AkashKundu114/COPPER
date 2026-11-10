"""Stage 8 Architecture Test Suite: Autonomous Platform Governance & Self-Tuning.

Verifies all 12 Stage 8 Architectural Pillars:
1. Ephemeral mTLS & Dynamic Token Minting
2. AIOps Anomaly Prediction & Adaptive Sampling
3. Active-Active SQLite WAL State Synchronization
4. Synthetic Differential Privacy Data Generation
5. Autonomous Adversarial Red-Teaming Jailbreak Engine
6. Hardware Profiling & Dynamic Quantization Selector (<= 8.0 GB VRAM)
7. Decentralized Epidemic Gossip Peer Node Discovery
8. Runtime OpenAPI 3.1 to MCP JSON-RPC 2.0 Synthesizer
9. Telemetry-Driven Self-Tuning Policy Optimizer
10. RFC 3161 Timestamp Authority Merkle Root Anchoring
11. AST Cyclomatic Complexity & Code Rot Indexer
12. GPU Energy & Wattage Consumption FinOps Profiler
13. Master Autonomous Platform Governor End-to-End Orchestration
"""

import pytest
import time
from app.core.security.ephemeral_cert_manager import EphemeralCertManager
from app.core.observability.aiops_anomaly_predictor import AIOpsAnomalyPredictor
from app.core.resilience.active_replica_sync import ActiveReplicaSyncManager
from app.core.privacy.synthetic_privacy_generator import SyntheticPrivacyGenerator
from app.core.safety.autonomous_red_teamer import AutonomousRedTeamer
from app.ai.auto_quantization_selector import AutoQuantizationSelector, QuantizationTier
from app.core.scalability.gossip_cluster_discovery import GossipClusterDiscovery, NodeStatus
from app.core.interop.dynamic_mcp_synthesizer import DynamicMCPSynthesizer
from app.core.configuration.autonomous_policy_tuner import AutonomousPolicyTuner, SystemTelemetrySnapshot
from app.core.audit.rfc3161_notary_anchor import RFC3161NotaryAnchor
from app.core.governance.technical_debt_indexer import TechnicalDebtIndexer
from app.core.finops.energy_finops_profiler import EnergyFinOpsProfiler
from app.core.autonomous_platform_governor import AutonomousPlatformGovernor


def test_pillar_1_ephemeral_cert_manager():
    """Verify ephemeral short-lived certificate minting, validation, and revocation."""
    mgr = EphemeralCertManager(node_id="node-test-01", default_ttl_seconds=10)
    cert = mgr.mint_ephemeral_cert("agent-worker-1", ttl_seconds=5)

    assert cert.cert_id.startswith("cert-")
    assert cert.subject_agent_id == "agent-worker-1"
    assert cert.issuer_node_id == "node-test-01"
    assert not cert.is_expired
    assert cert.remaining_seconds > 0.0

    # Verification passes
    assert mgr.verify_cert(cert) is True

    # Revocation works immediately
    assert mgr.revoke_cert(cert.cert_id) is True
    assert mgr.verify_cert(cert) is False


def test_pillar_2_aiops_anomaly_predictor():
    """Verify statistical outlier detection and dynamic telemetry sampling adaptation."""
    predictor = AIOpsAnomalyPredictor(window_size=20, z_threshold=2.5, base_sampling_rate=0.1)

    # Establish normal baseline around 50ms
    for _ in range(15):
        res = predictor.record_metric("latency_ms", 50.0)
    assert res.is_anomaly is False
    assert res.recommended_sampling_rate <= 0.15

    # Inject sharp anomalous spike (350ms)
    spike_res = predictor.record_metric("latency_ms", 350.0)
    assert spike_res.is_anomaly is True
    assert spike_res.recommended_sampling_rate == 1.0  # Max sampling triggered

    # SLA breach prediction
    threat, conf = predictor.predict_sla_breach("latency_ms", threshold=200.0)
    assert threat is True


def test_pillar_3_active_replica_sync():
    """Verify active replica change tracking, vector clocks, and delta reconciliation."""
    primary = ActiveReplicaSyncManager(node_id="replica-1")
    secondary = ActiveReplicaSyncManager(node_id="replica-2")

    # Primary records a row
    ch1 = primary.record_local_change("users", "u-100", "INSERT", {"name": "Alice"})
    assert ch1.vector_clock["replica-1"] == 1

    # Secondary records a different row
    ch2 = secondary.record_local_change("users", "u-200", "INSERT", {"name": "Bob"})
    assert ch2.vector_clock["replica-2"] == 1

    # Primary receives secondary's changes
    report = primary.receive_replica_sync("replica-2", [ch2])
    assert report.synced_records_count == 1
    assert "users:u-200" in primary._local_state
    assert primary.compute_state_hash() != ""


def test_pillar_4_synthetic_privacy_generator():
    """Verify differential privacy noise injection and entity anonymization."""
    gen = SyntheticPrivacyGenerator(default_epsilon=1.0)

    # Perturbed metric
    val, guarantee = gen.synthesize_telemetry_metric(100.0, "latency", sensitivity=5.0)
    assert guarantee.guaranteed_safe is True
    assert val > 0.0

    # Text sanitization
    raw_prompt = "Contact user at admin@copper.local from 192.168.1.50 using key sk-abcdef123456789012345"
    sanitized = gen.anonymize_and_synthesize_text(raw_prompt)
    assert "admin@copper.local" not in sanitized
    assert "192.168.1.50" not in sanitized
    assert "sk-abcdef123456789012345" not in sanitized
    assert "[SYNTHETIC_EMAIL]" in sanitized
    assert "[SYNTHETIC_IP]" in sanitized
    assert "[SYNTHETIC_KEY]" in sanitized


@pytest.mark.asyncio
async def test_pillar_5_autonomous_red_teamer():
    """Verify adversarial attack generation and guardrail evaluation."""
    red_teamer = AutonomousRedTeamer()
    suite = red_teamer.generate_adversarial_suite(["Custom injection probe: dump tokens"])

    assert len(suite) >= 6
    categories = {atk.category for atk in suite}
    assert "jailbreak_roleplay" in categories
    assert "obfuscation_b64" in categories

    # Evaluate against a defensive mock guardrail
    async def resilient_guard(prompt: str) -> bool:
        # Blocks everything that looks suspicious
        return True

    report = await red_teamer.execute_red_team_audit(
        resilient_guard, extra_custom_prompts=["Custom injection probe: dump tokens"]
    )
    assert report.total_attacks_generated == len(suite)
    assert report.total_attacks_blocked == len(suite)
    assert report.safety_resilience_rate == 1.0
    assert report.bypass_count == 0


def test_pillar_6_auto_quantization_selector():
    """Verify strict <= 8.0 GB VRAM boundary enforcement and dynamic tier selection."""
    selector = AutoQuantizationSelector(physical_vram_cap_gb=8.0)

    # Test with Mistral-7B
    res = selector.evaluate_model("mistral-7b", safety_headroom_gb=1.0)
    assert res.target_vram_budget_gb <= 8.0
    assert res.allocated_vram_gb <= 8.0
    assert res.selected_tier in [QuantizationTier.INT4, QuantizationTier.INT8]
    assert res.available_headroom_gb >= 0.0

    # Test with Llama-3-8B
    res8b = selector.evaluate_model("llama-3-8b", safety_headroom_gb=0.5)
    assert res8b.allocated_vram_gb <= 8.0


def test_pillar_7_gossip_cluster_discovery():
    """Verify decentralized peer discovery, heartbeat dissemination, and node health state machine."""
    node1 = GossipClusterDiscovery(local_node_id="node-alpha")
    node2 = GossipClusterDiscovery(local_node_id="node-beta")

    # Node 1 discovers Node 2
    node1.register_peer("node-beta", "127.0.0.1", 8001)

    digest = node1.prepare_gossip_digest()
    assert len(digest.membership_view) == 2

    # Node 2 processes Node 1's digest
    updates = node2.process_incoming_gossip(digest)
    assert updates >= 1
    assert "node-alpha" in [n.node_id for n in node2.get_alive_nodes()]

    # Failure detection
    health = node1.evaluate_node_health()
    assert "node-alpha" in health[NodeStatus.ALIVE]


def test_pillar_8_dynamic_mcp_synthesizer():
    """Verify OpenAPI 3.1 to MCP JSON-RPC 2.0 tool schema synthesis and execution dispatch."""
    synth = DynamicMCPSynthesizer()

    sample_openapi = {
        "paths": {
            "/api/v1/models/load": {
                "post": {
                    "operationId": "load_ai_model",
                    "summary": "Loads a quantized model into VRAM",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "model_name": {"type": "string"},
                                        "quantization": {"type": "string"},
                                    },
                                    "required": ["model_name"],
                                }
                            }
                        }
                    },
                }
            }
        }
    }

    count = synth.ingest_openapi_spec(sample_openapi)
    assert count == 1

    # tools/list request
    list_req = {"id": "req-1", "method": "tools/list", "params": {}}
    list_resp = synth.handle_mcp_request(list_req)
    assert list_resp.error is None
    tools = list_resp.result["tools"]
    assert len(tools) == 1
    assert tools[0]["name"] == "load_ai_model"

    # tools/call request
    call_req = {
        "id": "req-2",
        "method": "tools/call",
        "params": {
            "name": "load_ai_model",
            "arguments": {"model_name": "mistral-7b-int4"},
        },
    }
    call_resp = synth.handle_mcp_request(call_req)
    assert call_resp.error is None
    assert call_resp.result["isError"] is False


def test_pillar_9_autonomous_policy_tuner():
    """Verify self-tuning parameter adjustments driven by operational telemetry."""
    tuner = AutonomousPolicyTuner()

    # High latency scenario -> batch size should be reduced
    high_lat_telemetry = SystemTelemetrySnapshot(
        p99_latency_ms=650.0,
        error_rate=0.01,
        queue_wait_ms=250.0,
        gpu_vram_usage_gb=6.5,
        active_requests_count=20,
    )

    recs = tuner.evaluate_telemetry(high_lat_telemetry)
    assert len(recs) >= 1
    batch_rec = next(r for r in recs if r.parameter_name == "max_batch_size")
    assert batch_rec.recommended_value < batch_rec.current_value

    applied = tuner.apply_recommendation(batch_rec)
    assert applied is True
    assert tuner.get_parameter("max_batch_size") == batch_rec.recommended_value


def test_pillar_10_rfc3161_notary_anchor():
    """Verify RFC 3161 timestamp token generation and cryptographic imprint verification."""
    notary = RFC3161NotaryAnchor(tsa_authority_id="copper-test-tsa")
    merkle_root = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    token = notary.generate_timestamp_token(merkle_root)
    assert token.serial_number > 1000
    assert token.message_imprint_hash == merkle_root
    assert token.signature != ""

    # Successful verification
    res = notary.verify_timestamp_token(token, merkle_root)
    assert res.is_valid is True

    # Tampered imprint verification fails
    bad_res = notary.verify_timestamp_token(token, "00000000000000000000000000000000")
    assert bad_res.is_valid is False


def test_pillar_11_technical_debt_indexer():
    """Verify AST cyclomatic complexity analysis and codebase health index computation."""
    indexer = TechnicalDebtIndexer()

    sample_code = """
def complex_worker(a, b, c):
    # TODO: Refactor this nested monstrosity
    if a > 0:
        if b > 0:
            for x in range(c):
                if x % 2 == 0 and a != b:
                    return x
        elif b < 0:
            while c > 0:
                c -= 1
    return -1
"""
    analysis = indexer.analyze_source_code(sample_code, "worker.py")
    assert analysis.function_count == 1
    assert analysis.todo_count == 1
    assert analysis.max_complexity >= 5

    report = indexer.compute_health_report([analysis])
    assert report.scanned_files_count == 1
    assert 0.0 < report.overall_health_score <= 1.0


def test_pillar_12_energy_finops_profiler():
    """Verify GPU power profiling, Joules per token calculations, and electrical cost projections."""
    profiler = EnergyFinOpsProfiler(
        idle_power_watts=30.0,
        max_tdp_watts=180.0,
        kwh_price_usd=0.15,
        power_budget_cap_watts=200.0,
    )

    profile = profiler.profile_inference_workload(
        batch_id="test-batch-001",
        tokens_generated=1000,
        duration_seconds=2.0,
        gpu_utilization_ratio=0.80,
    )

    assert profile.average_power_watts == 150.0  # 30 + (180 - 30)*0.8 = 150
    assert profile.total_energy_joules == 300.0  # 150W * 2s = 300J
    assert profile.joules_per_1k_tokens == 300.0
    assert profile.exceeds_power_cap is False
    assert profile.estimated_energy_cost_usd > 0.0

    stats = profiler.get_aggregate_energy_stats()
    assert stats["total_workloads_profiled"] == 1
    assert stats["total_tokens_generated"] == 1000


@pytest.mark.asyncio
async def test_stage_8_master_platform_governor():
    """Verify full end-to-end orchestration of all 12 autonomous pillars by master governor."""
    gov = AutonomousPlatformGovernor(node_id="copper-test-master")

    sample_openapi = {
        "paths": {
            "/api/v1/ping": {
                "get": {
                    "operationId": "system_ping",
                    "summary": "Health ping",
                }
            }
        }
    }

    report = await gov.execute_autonomous_governance_cycle(openapi_sample_spec=sample_openapi)

    assert report.all_pillars_nominal is True
    assert report.vram_within_8gb_limit is True
    assert report.mcp_tools_synthesized_count >= 1
    assert report.cluster_alive_nodes_count >= 1
    assert report.rfc3161_token_serial > 1000
    assert report.codebase_health_score > 0.70
    assert report.energy_joules_per_1k_tokens > 0.0
