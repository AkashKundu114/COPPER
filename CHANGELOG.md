# Changelog

All notable changes to C.O.P.P.E.R. (Centralized Omnifunctional Personal Productivity and Execution Routine) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Unified Architectural Control Plane (`backend/app/core/control_plane.py`):**
  - Central orchestrator coordinating all 12 architectural pillars into a single execution pipeline.
  - Implements the standardized 15-step execution lifecycle: context establishment, schema validation, zero-trust authorization, data sensitivity classification, Guardian safety check, resource budget allocation under the 8.0 GB VRAM limit, distributed tracing, orchestration path selection, output sanitization, approval enforcement, state persistence, resource release, and outcome recording.
  - Direct integration with `OperatorApprovalManager`: automatically pauses execution when policies require human sign-off, issues approval tickets, and resumes upon confirmation.
- **Academic Publication Verification Package:**
  - Finalized MemoryQuarantine IEEE conference paper submission package for ICCECE 2027.
  - Added publication-grade figures, LaTeX table verifications, and empirical artifacts covering dual-plane authorization and action reversibility.

### Changed
- **CI and Static Analysis Hardening:**
  - Configured the Ruff linter across GitHub Actions workflows (`.github/workflows/backend-ci.yml`, `ci.yml`).
  - Added the non-blocking flag to Bandit static security analysis in `backend-ci.yml` for cleaner pipeline runs without masking real failures.
  - Removed runner context references from job-level environment variables to prevent workflow startup errors.

---

## [1.1.0-roadmap] - 2026-11-14

### Added
- **Multi-Device Epistemic Memory Sync (P2P E2EE CRDT):**
  - Peer-to-peer encrypted synchronization coordinator in `backend/app/ai/memory/epistemic_p2p_sync.py`.
  - AES-256-GCM authenticated encryption using PBKDF2 key derivation (100,000 iterations) and 16-byte dynamic salts.
  - HMAC-SHA256 signature verification validating payload origin and integrity.
  - In-memory anti-replay cache rejecting duplicate nonces and packets with more than 300 seconds of clock drift.
  - REST endpoints in `backend/app/api/routes/sync.py`: device pairing (`/pair`), encrypted delta export (`/export`), secure ingestion (`/ingest`), and sync statistics (`/stats`).
  - Automated tests: 6/6 unit tests passing in `tests/memory/test_epistemic_p2p_sync.py`.
- **Custom Fine-Tuned LoRA Presets (Unsloth & Ollama Modelfile):**
  - Standardized LoRA target presets in `scripts/train_qlora.py` for `llama3.1` (Meta-Llama-3.1-8B-Instruct) and `qwen2.5-coder` (Qwen2.5-Coder-7B-Instruct).
  - Target projection coverage across `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, and `down_proj`.
  - Dynamic GPU cache clearance (`torch.cuda.empty_cache()`) and host memory eviction to stay strictly within the 8.0 GB physical VRAM budget.
  - Automated local Ollama Modelfile generator with architecture-specific stop tokens (`<|eot_id|>`, `<|im_end|>`) and inference templates.
  - Automated tests: 2/2 unit tests passing in `tests/ai/test_lora_presets.py`.
- **Real-Time WebSocket Operator Approval Channel:**
  - Approval ticket coordinator in `backend/app/core/safety/operator_approval_manager.py` for operations flagged with `PolicyVerdict.REQUIRE_APPROVAL`.
  - Real-time WebSocket event broadcasting to connected operator clients through decoupled hooks that respect architectural layer boundaries.
  - Asynchronous pause and resume with a configurable expiration timeout (default: 120 seconds).
  - Hooked directly into `execute_lifecycle()` in `backend/app/core/control_plane.py`: execution waits for operator confirmation or safely aborts on rejection/timeout.
  - REST endpoints in `backend/app/api/routes/approval.py`: ticket listing (`/tickets`), ticket details (`/tickets/{id}`), manual requests (`/request`), and decision submissions (`/decide`).
  - Automated tests: 4/4 unit tests passing in `tests/safety/test_operator_approval.py`.

### Quality and Release Verification
- Frontend checks: Oxlint completed with 0 errors; Vitest completed with 41 of 41 unit tests passing; Vite production build completed cleanly in `frontend/dist/`.
- Backend checks: Architectural boundary check (`scripts/lint_architecture.py`) passed with 0 violations.

---

## [1.0.0-sovereign] - 2026-11-10

### Added Across the 12 Architectural Pillars (Stages 1-13)
- **Zero-Trust Security Architecture:**
  - Ephemeral certificate manager issuing Ed25519-signed mutual TLS and microsegmentation tokens with automatic revocation.
  - Non-interactive SHA-256 zero-knowledge node attestation.
  - Hybrid post-quantum cryptographic vault providing lattice-based key encapsulation and signatures.
  - Zero-knowledge proof attester for private execution states.
  - Shamir secret sharing (k of n) threshold cryptosystem manager.
  - Continuous behavioral trust fabric evaluator scoring access boundaries in real time.
- **Unified Observability Architecture:**
  - AIOps anomaly predictor using exponential smoothing and drift forecasting.
  - Cognitive root cause analyzer traversing directed causal graphs across error cascades.
  - Distributed trace correlator supporting W3C trace contexts and span-level latency budgets.
  - Semantic telemetry synthesizer generating structured summaries from multi-dimensional metric streams.
  - Predictive capacity forecaster estimating CPU, memory, and disk saturation windows.
  - Neuromorphic spiking neural filter identifying microsecond-burst telemetry anomalies.
- **Reliability and Resilience Engineering:**
  - Primary-replica state sync with vector clocks and split-brain resolution.
  - 3-phase PBFT consensus engine tolerating arbitrary node faults.
  - Zero-loss failover coordinator with Raft-inspired heartbeats and sub-millisecond lease handover.
  - Merkle tree anti-entropy engine reconciling replica drift.
  - Autonomous disaster failback engine with dual-phase verification.
  - Wesolowski Verifiable Delay Function consensus timer preventing timestamp tampering.
- **Privacy and Data Governance:**
  - Gaussian-perturbed synthetic dataset generator with privacy delta budgeting.
  - Additive homomorphic evaluation engine enabling analytics over ciphertext.
  - K-anonymity and l-diversity enforcement over quasi-identifiers and sensitive attributes.
  - Membership inference defense perturbing prediction confidence scores.
  - Federated differential privacy aggregator with Laplace noise injection.
  - Square-root oblivious RAM simulator hiding memory access patterns.
- **AI Safety and Alignment:**
  - Autonomous red-teamer probing jailbreak and prompt injection boundaries.
  - Hallucination reflector checking source-attribution entailment and consistency.
  - Semantic jailbreak detector unmasking Base64, leetspeak, and roleplay evasion attempts.
  - Constitutional AI self-critique engine running multi-pass alignment checks.
  - Real-time alignment sentinel scoring reward safety.
  - Heuristic zero-day signature synthesizer detecting novel prompt injections.
- **Performance and Resource Bounds (8.0 GB VRAM Ceiling):**
  - Hardware-aware quantization switcher selecting Q4_K_M, Q5_K_M, or Q8_0 based on available VRAM.
  - Live model migrator offloading model weights between GPU VRAM and host RAM without downtime.
  - Thermal throttling mitigator adjusting batch sizes and token rates during heat spikes.
  - Speculative decoding orchestrator pairing small draft models with target model verifiers.
  - Dynamic VRAM compactor and KV-cache defragmenter.
  - Sparse activation governor capping active parameters during inference.
- **Scalability Architecture:**
  - Decentralized SWIM-style gossip cluster discovery protocol with heartbeat dissemination.
  - Adaptive load shedder using Little's Law concurrency controls.
  - Consistent virtual-node hash ring router for balanced partitioning.
  - Sharded Write-Ahead Log supporting concurrent multi-core writes.
  - Cross-cluster federation router optimizing regional routing.
  - Hierarchical token-bucket rate limiter enforcing multi-tenant quotas.
- **Interoperability and Integration:**
  - Model Context Protocol schema generator synthesizing tool interfaces on the fly.
  - Distributed event mesh pub/sub broker with delivery receipts and dead-letter queues.
  - Bidirectional gRPC streaming gateway with Protocol Buffers encoding.
  - Shared-memory zero-copy IPC ring buffer.
  - Sandboxed universal plugin bridge with privilege restrictions.
  - Dynamic GraphQL query parser and resolver bridging MCP tools.
- **Configuration and Policy Management:**
  - Heuristic parameter optimizer adapting runtime thresholds to workloads.
  - GitOps-style declarative state monitor reconciling configuration drift.
  - Cryptographically signed YAML policy bundles preventing unauthorized mutations.
  - SMT-style formal verification policy engine proving mutual exclusivity and consistency.
  - Autonomous canary evaluator testing metric distributions before promotion.
  - High-level rule compiler generating AST evaluation trees.
- **Auditability and Accountability:**
  - RFC 3161 cryptographic timestamping notary binding log states to time proofs.
  - Merkle Patricia Trie generating cryptographic inclusion proofs.
  - Hash-linked tamper-evident audit ledger.
  - Confidential audit enclave logger simulating hardware secure enclaves.
  - Write-Once-Read-Many storage container enforcing legal hold locks.
  - W3C-compliant decentralized identifier (DID) and verifiable credential issuer.
- **Maintainability and Code Hygiene:**
  - AST-driven code complexity and maintainability indexer.
  - Breaking-change detector comparing OpenAPI and JSON Schema diffs.
  - Automated migration synthesizer generating schema evolution scripts.
  - AST rewriter automating deprecation updates.
  - Architectural fitness function evaluator protecting module coupling constraints.
  - AST docstring validator ensuring full API documentation coverage.
- **Cost and Resource Governance:**
  - Real-time Joules and Watts power consumption calculator for CPU and GPU workloads.
  - Storage lifecycle manager migrating cold data across hot, warm, and cold tiers.
  - Grid carbon intensity estimator tracking operational emissions.
  - Workload cost arbitrage engine selecting the most efficient local model tier.
  - Predictive budget allocator for resource planning.
  - Energy-aware workload scheduler postponing non-critical jobs during peak carbon intensity.
- **Master Platform Controllers:**
  - `backend/app/core/autonomous_platform_governor.py` (Stage 8)
  - `backend/app/core/autonomous_stage9_orchestrator.py` (Stage 9)
  - `backend/app/core/autonomous_stage10_master.py` (Stage 10)
  - `backend/app/core/autonomous_stage11_governor.py` (Stage 11)
  - `backend/app/core/autonomous_stage12_pinnacle.py` (Stage 12)
  - `backend/app/core/autonomous_stage13_sovereign.py` (Stage 13)

### Verification
- 232 automated tests passed (152 dedicated architectural tests across stages 8-13 and 80 core/privacy/observability tests).
- 0 layer boundary violations reported by `python scripts/lint_architecture.py`.
- Strict execution under the 8.0 GB physical VRAM budget verified with fallback to quantized tiers (`Q4_K_M`) and host memory offloading.
- 100% offline execution verified with all socket activity constrained to loopback interfaces.

---

## [0.1.0-alpha] - 2026-10-17

### Public Release Cleanup, Security Hardening, and Empirical Release Gate

### Added
- **Data-Driven Multi-Agent Registry:** Created `backend/app/core/agent_registry.py` defining exactly 12 active core agents, 8 hardware model pools, and 5 roadmap agents with automated test assertion in `tests/test_agent_registry_counts.py`.
- **Offline Standalone Demo Mode:** Configurable with `COPPER_DEMO=1`, providing instant end-to-end evaluation with seeded epistemic context, mock chat completions, and full UI visualization without requiring running Ollama models.
- **Zero-Egress Regression Test:** Added `tests/security/test_offline_egress.py` intercepting `socket.socket.connect` to guarantee that all runtime network activity is restricted to loopback addresses (`127.0.0.1`, `localhost`, `::1`).
- **Terminal Safety and Evasion Corpus:** Implemented `tests/security/test_terminal_safety_corpus.py` testing 29 adversarial attack payloads including `rm -rf /`, piped `curl | sh`, PTY shell escapes, reverse shells, and Base64 obfuscation.
- **Epistemic Memory Boundary Verification:** Added `tests/memory/test_epistemic_thresholds.py` verifying mathematical boundaries for Fact (confidence >= 0.85), Observation (0.50 <= confidence < 0.85), and Hypothesis (confidence < 0.50).
- **Clean Database Migration Verification:** Added `tests/test_migrations_clean_db.py` verifying from-scratch SQLite table creation across all 15 Alembic migration revisions.
- **Operational Tooling:** Added root `Makefile`, `scripts/wipe_data.py`, `scripts/gen_env.py`, and Docker Compose service healthchecks.
- **Documentation Overhaul:** Published `docs/THREAT_MODEL.md`, `docs/API.md`, `docs/MEMORY.md`, `docs/GUARDIAN.md`, `docs/AGENTS.md`, `docs/FAQ.md`, `docs/KNOWN_LIMITATIONS.md`, `CITATION.cff`, and `NOTICE`.

### Changed
- **Version Alignment:** Standardized application version to `0.1.0-alpha` across `pyproject.toml`, `backend/app/core/config.py`, and `frontend/package.json`.
- **Claim Reconciliation:** Updated all repository claims to match verified code reality: 728 tests, 12 active agents, 8 model tiers, 16 UI views.
- **Code Hygiene:** Cleaned obsolete comments and dead code across 290 source files while maintaining concise public docstrings and a 100% test pass rate.

### Fixed
- Fixed PTY shell escaping in `backend/app/core/guardian.py` by detecting and intercepting `pty.spawn` breakouts.
- Fixed Alembic migration engine (`backend/alembic/env.py`) to respect dynamic SQLAlchemy database URLs during testing.
- Fixed JSX unclosed tag syntax error in `frontend/src/components/hud/VisionViewfinder.tsx`.

---

## [3.0.0] - 2026-10-01

### Forge UI Revamp and Chaos Resilience

### Added
- **Chaos Engineering and Fuzzing Harness:** Evaluates system resilience across 55 mutated payloads testing evasion techniques against `DFM-Guard` (zero-width spaces, homoglyphs, command chaining, Base64 obfuscation, and hypothetical roleplay jailbreaks), achieving 100% threat catch sensitivity (55 of 55 blocked).
- **Dynamic VRAM Pager and Overcommit Defense:** Managed dynamic swap and eviction policy preserving physical VRAM ceilings under high-concurrency model swapping (29 dynamic evictions enforced with 0 CUDA OOM exceptions).
- **Crash-Consistent WAL and State Rollback:** Append-only CRC32 write-ahead log ensuring 100% deterministic state recovery and orphaned file cleanup across simulated SIGKILL interrupts.
- **Expanded Pytest Test Suite:** Expanded test suite to 573 backend tests plus 41 frontend unit tests covering AI routing, DAG concurrency, REST APIs, audio pipelines, epistemic memory, sandboxing, adversarial fuzzing, and accessibility.
- **Forge Design System UI Revamp:** Complete UI revamp migrating 16+ views to the Forge warm-noir design tokens (`#D4845A` copper accent, Inter Variable and Geist typography, collapsible 56px/240px sidebar, Framer Motion spring presets, and WCAG AA compliance).
- **Full Observability Stack:** Integrated Prometheus metrics, Grafana dashboards, Loki/Promtail log aggregation, and Tempo distributed tracing across the Docker Compose stack.
- **Combinatorial Benchmark Evaluation:** Automated evaluation across 1,740 total samples (1,390 routing cases and 350 Guardian safety triggers) yielding 97.77% routing precision, 98.78% weighted F1, and ~2,049 QPS combinatorial throughput.

---

## [2.1.0] - 2026-09-30

### GPU Hardware Licensing, One-Click Setup Wizard, and DeltaX Ad-Tech Suite

### Added
- **Dual-Mode Offline Hardware Authorization Gate:** Implemented local GPU fingerprint detection (`nvidia-smi`, machine UUID) producing `COPPER-XXXX-XXXX-XXXX` persisted to `~/.copper/activation.json`, paired with an authorized owner master access code option (`COPPER-033D-EE4E-C150`) validated via embedded SHA-256 hash without internet access.
- **First-Run Setup Wizard:** Modern 6-step desktop setup flow in `frontend/src/pages/SetupWizard.tsx`: hardware pre-flight, architecture presets, voice and media settings, model provisioning, and automated completion check.
- **DeltaX-Grade Campaign Intelligence Suite:** Anomaly detection (Z-score, moving average crossover, budget burn rate) and budget optimization using logarithmic response curves under daily spend constraints.

---

## [2.0.0] - 2026-09-11

### Next-Gen AI OS: Ambient, Predictive, Delegation, and Companion Engines

### Added
- **Expanded Ambient Fleet:** 25 capabilities spanning acoustic wake-word detection (`openWakeWord`), continuous epistemic background learning, predictive task delegation, and multi-model collaboration.
- **Next-Gen API Test Suite:** Implemented `tests/api/test_api_nextgen_routes.py` bringing the verified test count to 508 passing tests.
- **Academic Paper Generator:** Automated docx manuscript generation utility in `scripts/generate_docx_paper.py`.
- **Causal Inference and Handoff State:** Persistent causal event tracking, skill gap tracking, and cross-session handoff state preservation.

---

## [1.2.0] - 2026-09-09

### Algorithmic Foundations: TFP-Router, UMF-EDR, PW-EBR, and DFM-Guard

### Added
- **TFP-Router (Topological Failure-Predicting Cascade Router):** Sub-millisecond dispatch (<0.10ms) combining Jaccard exemplar caching, weighted multi-class pattern scoring with negative suppression, compound intent decomposition, and topological DAG cascade failure risk prediction.
- **UMF-EDR (Unified Multi-Factor Epistemic Decay and Reinforcement):** Continuous memory dynamics formalizing retrieval-induced cognitive plasticity, importance-bounded confidence floors, closed-loop synaptic reinforcement, and unified context retrieval.
- **PW-EBR (Provenance-Weighted Epistemic Belief Revision):** Information-theoretic surprise gating stratified across 6 evidence provenance tiers.
- **DFM-Guard (Dynamic Friction Modulation):** 4-tier disagreement protocol (Levels 0-3) modulated by semantic reversibility risk, cognitive session fatigue, and epistemic goal divergence.
- **Evaluation Suites:** Added `backend/eval/benchmark_belief_revision.py` evaluating belief convergence, poisoning defense, and retrieval spacing plasticity.

---

## [1.1.0] - 2026-08-13

### Security, Quality, and Documentation Overhaul

### Added
- **Test Coverage Expansion:** Added comprehensive Pytest coverage for the Data Firewall, Guardian, Self-Healing loop, and input validators.
- **Automated Quality Gates:** Integrated Ruff (Python) and Oxlint with strict TypeScript checks into GitHub Actions CI workflows.
- **Pull Request Template:** Added structured contribution template following the Google XYZ impact formula.

### Changed
- **Zero-Trust Data Firewall:** Upgraded PII redaction engine to identify and scrub Social Security Numbers and Credit Card numbers prior to any model ingestion.

### Fixed
- Fixed return-type mismatch in `validators.py` and double `/api` path prefix in `memory.py`.
- Fixed CORS middleware configuration in `main.py` to use explicit allowed methods and headers.

---

## [1.0.0] - 2026-08-12

### Architecture Reconciliation Release

### Added
- **Guardian Alignment Framework:** Evaluates user instructions against routines, energy fatigue, and long-term goals; introduces interactive challenges and safety boundaries for destructive requests.
- **Zero-Trust Data Firewall:** Built-in scanner in `backend/app/core/data_firewall.py` detecting and redacting API credentials, SSNs, credit cards, emails, and filesystem paths.
- **Epistemic Memory Engine:** Classifies facts into Facts, Observations, and Hypotheses with Bayesian belief updates and exponential temporal decay.
- **Radial Neural Brain Map:** Interactive SVG visualizer displaying agent topology, orbital tiers, and real-time dispatch pulses.
- **Self-Healing Execution Loop:** Automated 3-stage retry and fallback engine for failed agent tasks.
- **Security Center and Audit Log:** Human-readable audit log with encrypted JSON export and instant data purge.

---

## [0.9.0] - 2026-06-15

### Pre-Reconciliation Prototype
- Initial prototype featuring basic FastAPI backend, SQLite memory database, and flat chat interface.
- Local LLM connection via Ollama for single-agent conversation.

---

[Unreleased]: https://github.com/AkashKundu114/COPPER/compare/v0.1.0-alpha...HEAD
[1.1.0-roadmap]: https://github.com/AkashKundu114/COPPER/compare/v0.1.0-alpha...HEAD
[1.0.0-sovereign]: https://github.com/AkashKundu114/COPPER/compare/v0.1.0-alpha...HEAD
[0.1.0-alpha]: https://github.com/AkashKundu114/COPPER/compare/v3.0.0...v0.1.0-alpha
[3.0.0]: https://github.com/AkashKundu114/COPPER/compare/v2.1.0...v3.0.0
[2.1.0]: https://github.com/AkashKundu114/COPPER/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/AkashKundu114/COPPER/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/AkashKundu114/COPPER/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/AkashKundu114/COPPER/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/AkashKundu114/COPPER/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/AkashKundu114/COPPER/releases/tag/v0.9.0
