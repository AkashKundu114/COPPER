# Controlled Ablation Studies & Experimental Protocol Design
**Target Venue:** IEEE International Conference on Cognitive Electronic Computing and Engineering (ICCECE 2027)  
**System Under Test:** C.O.P.P.E.R. (Cognitive Offline Partner for Personalized Execution & Reasoning)  
**Document ID:** `research_audit/13_ABLATION_AND_EXPERIMENT_PLAN.md`  
**Evaluation Standard:** IEEE Transactions on Consumer Electronics / IEEE Computer Society Experimental Rigor Guidelines  
**Status:** Definite Protocol Design & Pre-Registration  

---

## 1. Executive Summary & Purpose

A fatal vulnerability in the initial IEEE manuscript draft (`research/paper.tex`) is the presentation of monolithic system performance metrics without isolated, controlled ablation studies. The paper claims state-of-the-art results (e.g., 97.77% routing accuracy, 99.83% safety sensitivity, sub-millisecond dispatch) without demonstrating the isolated marginal contribution of each architectural component or delineating where the system fails under stress.

This document establishes the pre-registered, controlled ablation protocols for all four primary subsystems of C.O.P.P.E.R.:
1. **Routing Subsystem (TFP-Router):** Dissecting the 3-stage cascade (Regex, Jaccard Cache, Semantic Embedding, SLM Escalation).
2. **Memory Subsystem (Epistemic Memory & MemoryQuarantine):** Isolating temporal decay (UMF-EDR), belief revision (PW-EBR), and consequence authorization.
3. **Safety & Guardrails Subsystem (DFM-Guard):** Comparing static binary gating against linear scoring, logistic regression, and dynamic fatigue/conflict friction.
4. **Persistence & Crash Recovery Subsystem (Task WAL):** Benchmarking in-memory state against rollback journaling and write-ahead logging with checkpointing.

Each study specifies: **Formal Hypotheses ($H_0, H_1$), Baseline Configurations, Independent & Dependent Variables, Evaluation Datasets, Execution Protocols, Mathematical Formulations, Statistical Tests, and Confounder Controls.**

---

## 2. Subsystem 1: Routing Engine (TFP-Router Ablation)

### 2.1 Research Problem & Context
The current routing architecture (`backend/app/ai/orchestration/agent_router.py:600-750`) cascades across:
- **Stage 0:** Fast Learned Route Memory Cache (Jaccard token similarity $\ge 0.90$).
- **Stage 1:** Heuristic Keyword & Regex Scoring (`COMPILED_KEYWORD_RULES` spanning 12 `AgentType` classes).
- **Stage 2:** Micro-LLM / SLM Semantic Fallback (when routing entropy $\mathcal{H} \ge \tau_{\text{entropy}}$ or top margin $\Delta_{\text{score}} < \tau_{\text{margin}}$).

While `paper.tex` claims 97.77% accuracy on a curated 1,390-sample dataset, empirical re-evaluation against the 12,204-sample perturbed dataset (`backend/eval/benchmark_report.md:11`) demonstrates a precipitous collapse to **56.87% accuracy** (Weighted F1: 57.1%), caused by rigid regex failure under conversational affixes and out-of-scope intent classes (`behavior`, `voice`).

### 2.2 Ablation Configurations (6 Tiers)
| Tier ID | Strategy Name | Operational Description |
| :--- | :--- | :--- |
| **C1** | `Regex-Only` | Disables cache and fallback; routes purely via `COMPILED_KEYWORD_RULES`. |
| **C2** | `Cache-Only` | Disables keyword rules; matches queries strictly against `DynamicRoutingMemory` (Jaccard $\ge 0.85$). |
| **C3** | `Regex + Cache` | Current Stage 0 + Stage 1 CPU implementation (Jaccard cache hit -> Regex score). |
| **C4** | `Semantic-Embed` | Pure dense retrieval using local embeddings (`nomic-embed-text-v1.5` cosine similarity against agent intent centroids). |
| **C5** | `Micro-LLM-Only` | Escalates 100% of queries to local quantized SLM (`Qwen2.5-1.5B-Instruct` zero-shot prompt classification). |
| **C6** | `Full-Cascade` (Proposed) | Stage 0 (Cache) -> Stage 1 (Regex) -> Stage 1.5 (Semantic Embed if entropy $\mathcal{H} > 0.65$) -> Stage 2 (SLM if margin $< 0.15$). |

### 2.3 Formal Hypotheses
- **$H_{0, \text{Acc}}$:** The Full Cascade (C6) does not provide a statistically significant improvement in Top-1 routing accuracy over the Regex+Cache baseline (C3) under perturbed out-of-distribution queries ($p \ge 0.01$).
- **$H_{1, \text{Acc}}$:** C6 achieves $\ge 88.0\%$ Top-1 accuracy on perturbed queries, significantly outperforming C3 ($p < 0.001$, McNemar test).
- **$H_{0, \text{Lat}}$:** C6 incurs an interactive latency penalty exceeding the human conversational perception threshold ($P_{95} > 50\text{ ms}$).
- **$H_{1, \text{Lat}}$:** By filtering $\ge 80\%$ of queries at Stages 0 and 1, C6 maintains an amortized median latency $P_{50} < 1.0\text{ ms}$ and $P_{95} < 25\text{ ms}$ on consumer CPU.

### 2.4 Datasets & Workload Profiles
1. **Curated Handcrafted Benchmark ($D_{\text{curated}}$, $N = 1,390$):**
   `backend/eval/datasets/routing/master_routing_dataset.json` (170 automation, 120 chat, 160 coding, 177 document, 132 image, 142 planner, 193 reminder, 176 research, 120 vision).
2. **Perturbed Synthetic Benchmark ($D_{\text{perturbed}}$, $N = 12,204$):**
   `backend/eval/datasets/partitions/master_routing/test.jsonl` containing syntactic modifiers, noise prefixes, and compound instructions.
3. **Out-of-Scope Intent Shift Corpus ($D_{\text{OOD}}$, $N = 1,500$):**
   500 multi-intent queries, 500 domain-shifted health/behavior queries, and 500 audio/voice queries to test graceful fallback.

### 2.5 Metrics & Statistical Testing
- **Metrics:** Top-1 Accuracy, Macro-F1, Weighted F1, Out-of-Distribution Rejection Rate, Throughput (QPS), Latency Distribution ($P_{50}, P_{90}, P_{95}, P_{99}$ in ms), CPU Core Utilization (%), GPU VRAM Usage (MB).
- **Statistical Tests:**
  - McNemar's test for paired classification accuracy between C3 and C6 across the 12,204 queries.
  - Wilcoxon signed-rank test for paired latency distributions.
  - 95% Wilson score confidence intervals for per-class precision and recall.

### 2.6 Confounder Controls
- **Cold-Start vs Warm Cache:** Ensure cache is flushed between independent runs; benchmark cache warm-up curves from 0 to 1,000 queries.
- **CPU Thermal Throttling:** Pin benchmark process to performance cores (P-cores) using Windows process affinity (`psutil.Process().cpu_affinity([0, 2, 4, 6])`); verify CPU package temperature $< 75^\circ\text{C}$.

---

## 3. Subsystem 2: Memory & Belief Revision Subsystem

### 3.1 Research Problem & Context
C.O.P.P.E.R. implements:
- **UMF-EDR (`memory_manager.py:30-45`):** Temporal decay governed by Ebbinghaus forgetting curves modified by ACT-R spacing:
  $$\lambda_{\text{eff}} = \frac{\lambda_{\text{base}}}{1 + \beta \ln(1 + R_{\text{count}})}, \quad C(t) = \max\left(C_{\text{floor}}, C_0 \cdot e^{-\lambda_{\text{eff}} \cdot \Delta t}\right)$$
- **PW-EBR (`memory_manager.py:64-90`):** Surprise-gated log-odds belief updating:
  $$L_{\text{prior}} = \ln\left(\frac{C_{\text{prior}}}{1 - C_{\text{prior}}}\right), \quad \Delta L = \text{polarity} \cdot \gamma_s \cdot \min(3.5, -\log_2(1 - |C_{\text{prior}} - y^*| + \epsilon) \cdot \text{scale})$$
- **MemoryQuarantine (`research/notes/memory_quarantine.md`):** Dual-plane action authorization:
  $$\text{Authority}(m, a) = \gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}_{\text{action}}(a))$$

The current manuscript validated PW-EBR on only $N=6$ toy scenarios (`backend/eval/benchmark_belief_revision.py`). A true archival study requires evaluating memory resilience against delayed prompt injection and memory poisoning.

### 3.2 Ablation Configurations (6 Tiers)
| Tier ID | Strategy Name | Operational Description |
| :--- | :--- | :--- |
| **M0** | `No-Memory` | Stateless baseline; no persistent storage across sessions. |
| **M1** | `Vector-RAG` | Uncalibrated dense vector retrieval (ChromaDB cosine similarity); memories remain static with confidence 1.0. |
| **M2** | `Recency-LWW` | Last-Write-Wins; latest memory entry unconditionally overwrites prior beliefs on collision. |
| **M3** | `Epistemic-EBR` | PW-EBR log-odds belief revision enabled, but temporal decay disabled ($\lambda = 0$). |
| **M4** | `UMF-Decay-Only` | Temporal decay enabled ($\lambda > 0$, ACT-R spacing), but belief revision uses linear additions without surprise gating. |
| **M5** | `MemoryQuarantine` (Proposed) | Full integration: UMF-EDR + PW-EBR + Consequence-Coupled Authorization Gate $\text{Authority}(m, a)$. |

### 3.3 Formal Hypotheses
- **$H_{0, \text{Poison}}$:** MemoryQuarantine (M5) does not reduce the Attack Success Rate (ASR) of persistent delayed poisoning compared to Vector-RAG (M1) ($p \ge 0.01$).
- **$H_{1, \text{Poison}}$:** M5 reduces ASR from $> 90\%$ in M1 to $< 5\%$ in M5 ($p < 0.001$, Fisher's exact test).
- **$H_{0, \text{Utility}}$:** M5 causes a statistically significant degradation in Benign Task Success Rate (TSR) compared to Vector-RAG (M1).
- **$H_{1, \text{Utility}}$:** M5 maintains $\text{TSR} \ge 95.0\%$ with a False Quarantine Rate $\text{FQR} \le 5.0\%$.

### 3.4 Datasets & Workload Profiles
1. **CopperMemoryBench ($N = 160$ traces):**
   `research/experiments/memory_quarantine/copper_memory_bench.json` containing 100 adversarial traces across 5 attack vectors (`AV1_DirectInjection`, `AV2_IndirectToolPoisoning`, `AV3_DelayedActionSteering`, `AV4_BridgingSubversion`, `AV5_ContradictionFlood`) and 60 benign user preference/task traces.
2. **Long-Horizon Multi-Session Synthetics ($N = 500$ session steps):**
   Simulated 90-day interaction timeline with elapsed intervals $\Delta t \in [1, 90]$ days, assessing factual stability versus obsolete belief decay.

### 3.5 Metrics & Statistical Testing
- **Metrics:** Attack Success Rate (ASR %), Threat Interception Rate (TIR %), Benign Task Success Rate (TSR %), False Quarantine Rate (FQR %), Operator Confirmation Ratio (OCR confirmations/turn), Retrieval Overhead Latency ($P_{95}$ ms).
- **Statistical Tests:**
  - Pairwise McNemar tests between M5 and baselines (M0--M4) for threat interception.
  - Two-way ANOVA evaluating interaction between Attack Vector Category and Memory Strategy.
  - Wilson score 95% confidence intervals on TSR and TIR.

### 3.6 Confounder Controls
- **Embedding Invariance:** Ensure identical embedding models (`nomic-embed-text-v1.5`) across M1--M5.
- **Trace Ordering:** Counterbalance trace execution order to eliminate memory cache leakage across test runs.

---

## 4. Subsystem 3: Safety & Friction Subsystem (DFM-Guard Ablation)

### 4.1 Research Problem & Context
`paper.tex:620-655` claims that dynamic continuous friction:
$$\mathcal{F}_{\text{dynamic}}(a) = 3.0 \cdot \sigma\left(w_R \cdot R(a) + w_F \cdot F_{\text{fatigue}} + w_G \cdot G_{\text{conflict}} - \text{bias}\right)$$
eliminates binary guardrail paralysis while preventing confirmation fatigue. However, `calibrate_friction.py` tuned parameters on only 350 curated samples, while on 11,501 synthetic threat samples, the engine suffered **770 unblocked breaches (6.7% FNR)** (`backend/eval/benchmark_report.md:59`).

### 4.2 Ablation Configurations (6 Tiers)
| Tier ID | Strategy Name | Operational Description |
| :--- | :--- | :--- |
| **S0** | `Static-Binary` | Conventional binary regex blocklist (e.g., Llama Guard / NeMo style hard interdiction); accept or drop. |
| **S1** | `Linear-Score` | Unbounded linear weighted sum $S = w_R R + w_F F + w_G G - b$; thresholded at $S \ge 1.5$. |
| **S2** | `Logistic-Reg` | Standard logistic regression producing probability $P(\text{unsafe}) \in [0, 1]$; binary cutoff at 0.50. |
| **S3** | `DFM-No-Fatigue` | DFM-Guard with $w_F = 0$; friction responds only to reversibility and goal conflict. |
| **S4** | `DFM-No-Conflict` | DFM-Guard with $w_G = 0$; friction responds only to reversibility and fatigue. |
| **S5** | `Full-DFM` (Proposed) | Full continuous 4-tier friction protocol (Execute, Nudge, Challenge, Boundary) governed by calibrated parameters ($w_R=2.8, w_F=1.8, w_G=2.2, b=3.5$). |

### 4.3 Formal Hypotheses
- **$H_{0, \text{FPR}}$:** Dynamic friction modulation (S5) does not decrease operator confirmation fatigue compared to static binary thresholding (S0) on benign tasks ($p \ge 0.01$).
- **$H_{1, \text{FPR}}$:** S5 reduces unnecessary confirmation interruptions by $\ge 60\%$ on benign developer tasks while maintaining zero false negatives on destructive commands.
- **$H_{0, \text{Fatigue}}$:** Incorporating the session cognitive fatigue parameter $w_F \cdot F_{\text{fatigue}}$ produces no measurable difference in challenge rate during extended sessions ($\ge 4$ hours).
- **$H_{1, \text{Fatigue}}$:** S5 progressively escalates scrutiny on ambiguous actions as session fatigue rises, intercepting $\ge 30\%$ more careless operator approvals under high simulated fatigue.

### 4.4 Datasets & Workload Profiles
1. **Curated Threat & Benign Suite ($N = 350$):**
   `tests/data/adversarial_guardian_350.json` (230 threats, 120 benign).
2. **Scaled Partition Threat Suite ($N = 11,501$):**
   `backend/eval/datasets/partitions/threats/test.jsonl` (homoglyphs, obfuscated shell commands, base64 payloads, privilege escalations).
3. **Simulated Operator Workload ($N = 1,000$ operations):**
   Synthetic multi-hour workflow with error injection rates ranging from $0.0$ to $0.40$ and session durations from $0.5$ to $8.0$ hours.

### 4.5 Metrics & Statistical Testing
- **Metrics:** Threat Interception Rate (TPR %), Benign False Alarm Rate (FPR %), Area Under ROC Curve (AUC-ROC), Operator Confirmation Burden (prompts/hour), Mean Decision Latency (µs).
- **Statistical Tests:**
  - DeLong test for comparing ROC curves between S1, S2, and S5.
  - Exact Clopper-Pearson 95% confidence intervals for sensitivity and specificity.
  - Paired t-test on confirmation burden across simulated fatigue regimes.

### 4.6 Confounder Controls
- **Obfuscation Normalization:** Ensure `normalize_adversarial_text` (`guardian.py:37-75`) is applied identically across all configurations to isolate scoring logic from text pre-processing.

---

## 5. Subsystem 4: Persistence & Crash Recovery Subsystem

### 5.1 Research Problem & Context
`paper.tex:119` claims crash-consistent recovery for multi-agent DAGs using Write-Ahead Logging (WAL) with monotonic Log Sequence Numbers (LSNs) and CRC32 checksums (`backend/app/ai/orchestration/wal_executor.py`), validated with 5/5 recoveries. However, a 5-sample trial is statistically underpowered (95% Clopper-Pearson CI: [47.8%, 100.0%]). A rigorous experimental protocol requires 500+ fault injection iterations.

### 5.2 Ablation Configurations (3 Tiers)
| Tier ID | Strategy Name | Operational Description |
| :--- | :--- | :--- |
| **P0** | `SQLite-InMemory` | SQLite `:memory:` database without disk persistence; simulates pure RAM agent memory. |
| **P1** | `SQLite-Rollback` | Traditional SQLite Rollback Journal (`PRAGMA journal_mode=DELETE; PRAGMA synchronous=FULL;`). |
| **P2** | `SQLite-WAL-Checkpt` (Proposed) | SQLite WAL mode (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`) combined with TaskWAL (`wal_executor.py`) monotonic LSNs and CRC32 checkpointing. |

### 5.3 Formal Hypotheses
- **$H_{0, \text{Throughput}}$:** WAL with asynchronous checkpointing (P2) does not increase write transaction throughput compared to rollback journaling (P1) ($p \ge 0.01$).
- **$H_{1, \text{Throughput}}$:** P2 achieves $\ge 3.5\times$ higher transaction throughput (TPS) than P1 on concurrent multi-agent read/write workloads.
- **$H_{0, \text{Recovery}}$:** In abrupt process termination under uncommitted mutations, P2 does not achieve 100% state recovery and zero dangling file mutations.
- **$H_{1, \text{Recovery}}$:** Across $N = 500$ randomized fault injections, P2 achieves $100.0\%$ clean recovery with exact compensating rollback ($p < 0.001$).

### 5.4 Datasets & Workload Profiles
1. **Multi-Agent DAG Synthetic Workload ($N = 500$ DAGs):**
   Generated DAGs spanning 3 to 12 task nodes with dependencies, file mutations, database writes, and inter-agent messages.
2. **Chaos Fault Injection Engine (`test_chaos_and_fuzzing.py`):**
   Randomly timed `os._exit(1)` and hard process SIGKILL triggers injected at 4 lifecycle phases: (1) Pre-task commit, (2) During disk fsync, (3) Mid-checkpoint, (4) During compensating rollback.

### 5.5 Metrics & Statistical Testing
- **Metrics:** Recovery Success Rate (%), Mean Time to Recover (MTTR in ms), Transaction Throughput (TPS / IOPS), Orphaned File Mutation Count, Storage Amplification Ratio (WAL size vs DB size).
- **Statistical Tests:**
  - One-sided exact binomial test for recovery reliability (target $100\%$ with lower 95% bound $\ge 99.4\%$).
  - Mann-Whitney U test for recovery latency between P1 and P2.

### 5.6 Confounder Controls
- **Disk Write Caching:** Disable Windows OS write caching on the benchmark volume during tests or use explicit `FILE_FLAG_WRITE_THROUGH` to eliminate non-deterministic OS cache flushes.

---

## 6. Master Summary Table of Ablation Protocols

| Subsystem | Baseline | Proposed Candidate | Primary Metric | Target Performance | Required Sample Size | Statistical Test |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Routing** | C3 (Regex+Cache) | C6 (Full Cascade) | Out-of-Distribution F1 | $\ge 88.0\%$ (vs 57.1%) | $N = 12,204$ | McNemar paired test ($p < 0.001$) |
| **Memory** | M1 (Vector-RAG) | M5 (MemoryQuarantine) | Delayed Poisoning ASR | $\le 5.0\%$ (vs $>90\%$) | $N = 160$ traces | Fisher's exact / McNemar ($p < 0.001$) |
| **Safety** | S0 (Static Binary) | S5 (Full DFM-Guard) | Benign False Alarm Rate | $\le 2.0\%$ with $0\%$ FNR | $N = 11,501$ threats + 1,000 benign | DeLong ROC-AUC & Clopper-Pearson |
| **Persistence** | P1 (Rollback Journal) | P2 (WAL + TaskWAL) | Write TPS & Recovery Rate | $\ge 3.5\times$ TPS, $100\%$ Rec | $N = 500$ crash runs | Binomial exact ($p < 0.001$) |

This pre-registered plan provides the empirical scaffolding required to upgrade C.O.P.P.E.R. into an unassailable research contribution for ICCECE 2027.
