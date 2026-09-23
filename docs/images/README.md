# C.O.P.P.E.R. Visual Asset Gallery & Figure Inventory

This directory contains the publication-grade figures, system architecture diagrams, and empirical benchmark charts for **C.O.P.P.E.R.** (Centralized Omnifunctional Personal Productivity and Execution Routine).

All figures are rendered at publication-standard **350 DPI** using scientific styling (pure white canvas `#ffffff`, professional typography, and colorblind-safe palettes).

---

## 1. Canonical System & Empirical Architecture Figures (Figures 1–15)

The table below maps the 15 canonical architecture and benchmark figures:  
> **Title:** *Sovereign Multi-Agent Operating Systems on Consumer Hardware via Cascade-Aware Routing and Epistemic Memory Plasticity*  
> **Author:** Akash Kundu — Independent Researcher & Systems Architect ([ORCID: 0009-0003-8246-7316](https://orcid.org/0009-0003-8246-7316))  

| Figure | Canonical Asset | Descriptive Alias | Section | Scientific Content & Significance |
| :---: | :--- | :--- | :--- | :--- |
| **Fig. 1** | `kundu1.png` | `fig8_system_architecture_topology.png` | §III Architecture | **System Architecture Topology & Bus Interconnect:** End-to-end air-gapped sovereign topology enforcing strict 3-tier isolation (Electron UI, FastAPI Orchestrator, Resident GGUF Model Pool) with zero external network egress. |
| **Fig. 2** | `kundu2.png` | `fig5_multi_agent_routing_matrix.png` | §III.A TFP-Router | **Multi-Agent Routing Confidence Matrix:** Intent classification heatmap across 9 specialized cognitive categories achieving 97.77% raw accuracy and 98.78% weighted F1 on 1,390 intent queries. |
| **Fig. 3** | `kundu3.png` | `fig3_latency_throughput_pareto.png` | §III.A TFP-Router | **Routing Latency vs. Throughput Pareto Curve:** Empirical Pareto optimal frontier mapping first-token latency vs sustained throughput from the sub-millisecond reflex tier to the heavy 14B cognitive tier. |
| **Fig. 4** | `kundu4.png` | `fig6_epistemic_memory_decay_dynamics.png` | §III.B UMF-EDR | **Epistemic Memory Half-Life & Friction Dynamics:** (a) UMF-EDR temporal decay half-lives across Facts, Observations, and Hypotheses. (b) PW-EBR surprise-gated Bayesian log-odds jumps following congruent vs incongruent evidence. |
| **Fig. 5** | `kundu5.png` | `fig7_guardian_firewall_safety_roc.png` | §III.C DFM-Guard | **Guardian Firewall Receiver Operating Characteristic (ROC):** Macro AUROC = 0.998 across 1,740 adversarial red-teaming evaluations with high-specificity operating window ($FPR \le 0.05$). |
| **Fig. 6** | `kundu6.png` | `data_firewall_pipeline.png` | §III.D Firewall | **Zero-Trust Data Firewall Verification Pipeline:** 16 compiled regex patterns across 4 security tiers, volatile Redis vaulting with 15-min TTL, and SHA-256 cryptographic provenance hashing. |
| **Fig. 7** | `kundu7.png` | `fig12_wal_crash_consistency.png` | §III.F WAL | **Write-Ahead Log (WAL) State Machine & Crash Recovery:** ARIES-style durability protocol enforcing synchronous physical `fsync`, CRC32 checksums, and 100% state recovery across simulated SIGKILL interruptions. |
| **Fig. 8** | `kundu8.png` | `self_healing_sentinel.png` | §III.G Sentinel | **Self-Healing Sentinel FSM & Auto-Remediation:** 3-stage autonomous health watchdog loop (surveillance, fallback model cascading, incident audit logging). |
| **Fig. 9** | `kundu9.png` | `fig11_vram_pager_and_concurrency.png` | §III.E Pager | **VRAM Weighted LRU Offloader & Concurrency State:** Multi-factor weighted LRU eviction with DAG lookahead prefetching maintaining strict $\le 8.0$ GB VRAM budget with zero CUDA OOM crashes. |
| **Fig. 10** | `kundu10.png` | `fig2_vram_memory_footprint.png` | §IV.E VRAM | **Memory Footprint by Allocation Category:** Physical GPU VRAM breakdown (4.5GB Core + 1.1GB Subagent + 0.9GB Context Cache + 1.3GB Safety Headroom) and 975MB host system RAM footprint. |
| **Fig. 11** | `kundu11.png` | `fig1_throughput_acceleration.png` | §IV.E Throughput | **Quantized Model Throughput Acceleration:** Empirical 14B speedup (+81% to +220%) and throughput spectrum across the specialized agent fleet on NVIDIA RTX 5060 Laptop GPU. |
| **Fig. 12** | `kundu12.png` | `fig13_chaos_fuzzing_and_hybrid_rrf.png` | §IV.D Chaos | **Chaos Engineering Fuzzing & Hybrid RRF Ranking:** (Left) 100.0% threat catch sensitivity across 5 evasion families. (Right) Symbol-Preserving Hybrid Reciprocal Rank Fusion achieving 0.96 MRR@10. |
| **Fig. 13** | `kundu13.png` | `fig4_kv_cache_layer_offload_study.png` | §IV.E KV Cache | **KV Cache Layer Offload vs. VRAM & Latency:** Quantization ablation study comparing f16 vs q8_0 vs q4_0 KV cache allocations on sustained generation throughput. |
| **Fig. 14** | `kundu14.png` | `fig9_context_scaling_vram_stability.png` | §IV.E Context | **Context Window Scaling & Memory Stability:** Context scaling behavior vs physical 8.12 GB VRAM ceiling, identifying the f16 CPU spill threshold. |
| **Fig. 15** | `kundu15.png` | `fig10_sovereign_evolution_loop.png` | §III.B Dreaming | **Sovereign Memory Consolidation Cycle (Dreaming Protocol):** Continuous offline trajectory capture, Bayesian distillation, synthetic curriculum generation, and edge companion persona adaptation. |

---

## 2. Hardware Telemetry & Empirical Profiling Charts

These figures provide granular performance and hardware diagnostic telemetry from the live benchmarking evaluation suite ([`backend/eval/benchmark.py`](../../backend/eval/benchmark.py)):

| Asset Filename | Description | Metric / Operating Environment |
| :--- | :--- | :--- |
| `latency_percentiles.png` | Sub-millisecond latency distribution across routing stages | P50: 0.238 ms, P90: 0.357 ms, P95: 0.379 ms, P99: 0.410 ms |
| `vram_memory_allocation.png` | Dedicated GPU VRAM allocation breakdown | RTX 5060 Laptop (8GB VRAM) with ~1.3GB headroom |
| `system_ram_footprint.png` | Host system RAM consumption profile | Active C.O.P.P.E.R. suite < 1.0 GB total RAM |
| `token_generation_throughput.png` | Generation & prompt evaluation throughput across model tiers | 185 T/s (1B) to 52 T/s (14B) on local GPU |
| `model_comparison_radar.png` | Multi-dimensional capability radar chart across 4 model families | Coding, Reasoning, Safety, Concurrency, and Low-Latency |
| `routing_accuracy_benchmark.png` | Intent classification accuracy and safety catch rates | 97.77% routing accuracy, 100% Guardian catch sensitivity |

---

## 3. Architecture & Subsystem Pipeline Visualizations

| Asset Filename | Pipeline / Subsystem | Key Mechanism |
| :--- | :--- | :--- |
| `audio_voice_pipeline.png` | Multimodal Voice & Ambient Pipeline | openWakeWord $\to$ Silero VAD $\to$ Whisper Turbo $\to$ Kokoro TTS |
| `document_generation_pipeline.png` | Executive Report Generation Engine | Multi-source synthesis, Markdown compiling, and PDF/DOCX export |
| `epistemic_memory_layers.png` | Epistemic Memory Layer Architecture | Fact / Observation / Hypothesis 3-tier classification hierarchy |
| `guardian_intervention_levels.png` | Guardian Alignment Protocol | 4-tier continuum: Level 0 (Execute) $\to$ Level 3 (Safety Boundary) |
| `nexus_dag_orchestration.png` | Nexus Multi-Agent DAG Orchestrator | Topological task decomposition with parallel dependency scheduling |
| `data_firewall_pipeline.png` | Zero-Trust Data Firewall Flow | Real-time PII tokenization and cryptographic audit hashing |
| `self_healing_sentinel.png` | Autonomous Self-Healing Sentinel | Watchdog FSM with automated model fallback and rollback recovery |

---

## 4. Generation & Reproduction Tooling

All figures can be deterministically regenerated at 350 DPI using the master script:
```bash
python research/generate_all_academic_figures.py
```
This script populates:
- `research/figures/` (manuscript figures `kundu1.png` – `kundu15.png`)
- `research/arxiv_package/figures/` (arXiv submission bundle)
- `docs/images/` (documentation gallery)
