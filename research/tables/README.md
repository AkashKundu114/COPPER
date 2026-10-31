# MemoryQuarantine: Academic Tables Compendium

This directory contains the standalone LaTeX (`.tex`) and Markdown (`.md`) tables for the MemoryQuarantine research paper:
> **"MemoryQuarantine: Consequence-Calibrated Persistent Memory Integrity for Local Tool-Using Agents"**
> Target Venue: *IEEE Conference on Computational Electromagnetics, Communication, and Edge Computing (ICCECE 2027)*

---

## Index of Tables

1. **[Table 1: Comprehensive Benchmark Results on CopperMemoryBench](#table-1-comprehensive-benchmark-results-on-coppermemorybench-n--160-traces)** ([`.tex`](table1_main_security_results.tex) | [`.md`](table1_main_security_results.md))
2. **[Table 2: Attack Success Rate (ASR) Across Attack Vectors](#table-2-attack-success-rate-asr-across-attack-vectors-n20-each)** ([`.tex`](table2_attack_vector_breakdown.tex) | [`.md`](table2_attack_vector_breakdown.md))
3. **[Table 3: Empirical Metric Reconciliation and Audit Provenance](#table-3-empirical-metric-reconciliation-and-audit-provenance)** ([`.tex`](table3_audit_reconciliation.tex) | [`.md`](table3_audit_reconciliation.md))
4. **[Table 4: Taxonomic Comparison of Agent Memory Architectures and Defenses](#table-4-taxonomic-comparison-of-agent-memory-architectures-and-defenses)** ([`.tex`](table4_related_work_matrix.tex) | [`.md`](table4_related_work_matrix.md))
5. **[Table 5: Immutable Provenance Hierarchy ($\gamma$) and Channel Trust Specifications](#table-5-immutable-provenance-hierarchy-gamma-and-channel-trust-specifications)** ([`.tex`](table5_provenance_hierarchy.tex) | [`.md`](table5_provenance_hierarchy.md))
6. **[Table 6: Threat Model Specification: Adversary Capabilities, Protected Assets, and Security Invariants](#table-6-threat-model-specification)** ([`.tex`](table6_threat_model_summary.tex) | [`.md`](table6_threat_model_summary.md))
7. **[Table 7: Empirical Hardware and Software Testbed Specification](#table-7-empirical-hardware-and-software-testbed-specification)** ([`.tex`](table7_experimental_testbed.tex) | [`.md`](table7_experimental_testbed.md))
8. **[Table 8: Formal Hypothesis Testing, Contingency Analysis, and Statistical Significance](#table-8-formal-hypothesis-testing-contingency-analysis-and-statistical-significance)** ([`.tex`](table8_statistical_significance.tex) | [`.md`](table8_statistical_significance.md))

---

### Table 1: Comprehensive Benchmark Results on CopperMemoryBench ($N = 160$ Traces)

| Strategy | ASR (%) $\downarrow$ | Exact 95% CI | TIR (%) $\uparrow$ | Benign TSR (%) $\uparrow$ | Exact 95% CI | FQR (%) $\downarrow$ | OCR (%) | Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$B_0$ (Flat RAG / None)** | 100.0% | [96.4%, 100.0%] | 0.0% | 100.0% | [94.0%, 100.0%] | 0.0% | 0.0% | $<0.001$ |
| **$B_1$ (Last-Write-Wins)** | 100.0% | [96.4%, 100.0%] | 0.0% | 100.0% | [94.0%, 100.0%] | 0.0% | 0.0% | $<0.001$ |
| **$B_2$ (Naive Bayes)** | 80.0% | [70.8%, 87.3%] | 20.0% | 100.0% | [94.0%, 100.0%] | 0.0% | 0.0% | $<0.001$ |
| **$B_3$ (Provenance-Only)** | 80.0% | [70.8%, 87.3%] | 20.0% | 100.0% | [94.0%, 100.0%] | 0.0% | 0.0% | 0.005 |
| **$M_5$ (MemoryQuarantine)** | **0.0%** | **[0.0%, 3.6%]** | **100.0%** | **100.0%** | **[94.0%, 100.0%]** | **0.0%** | **70.0%** | **0.005** |

---

### Table 2: Attack Success Rate (ASR) Across Attack Vectors ($N=20$ each)

| Threat Vector Class | Description | $B_0$ (Flat RAG) | $B_1$ (Last-Write) | $B_2$ (Naive Bayes) | $B_3$ (Prov-Only) | $M_5$ (MemoryQuarantine) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **AV1: Direct Chat Injection** | Untrusted conversational input plants imperative instruction | 100% | 100% | 100% | 100% | **0%** |
| **AV2: Indirect Tool Poisoning** | External API or web search snippet injects system override | 100% | 100% | 100% | 100% | **0%** |
| **AV3: Delayed Action Steering** | Subtle low-consequence bias escalated over sessions | 100% | 100% | 100% | **0%** | **0%** |
| **AV4: Bridging Subversion** | Payload splits instructions across benign & tainted fragments | 100% | 100% | 100% | 100% | **0%** |
| **AV5: Contradiction Flood** | Repeated adversarial assertions to ratchet confidence | 100% | 100% | **0%** | 100% | **0%** |

---

### Table 3: Empirical Metric Reconciliation and Audit Provenance

| Subsystem | Historical Unverified Claim | Recalculated Baseline Reality | Remediated Empirical Ground Truth |
| :--- | :--- | :--- | :--- |
| **TFP-Router** | 97.77% routing accuracy across 1,390 curated samples | 97.41% on 1,390 curated; collapses to 56.87% on scaled 12,204-query benchmark | Benchmark had 2,372 unmapped queries (`voice`, `behavior`) and regex caret bugs. Remediated via GPU neural router: **99.98% Top-1, 99.99% Weighted-F1** on RTX 5060 (1.425 ms P95). |
| **Guardian Safety** | 99.83% safety catch across 1,740 test cases | 100% on 350 curated; 93.3% on 11,501 scaled threats (770 breaches) | Historical 1,740 claim was unverified. Remediated via adversarial homoglyph/zero-width normalization: threat catch restored to **99.45%** (breaches reduced to 63). |
| **Belief Revision** | Provenance declared superior to LWW | Evaluated on toy $N=6$ synthetic scenarios | Replaced toy scenarios with 160-trace CopperMemoryBench and end-to-end physical execution with local models on an RTX 5060 GPU. |
| **Crash Recovery** | 100% crash consistency ($N=5$ trials) | $N=5$ had 95% CI of [47.8%, 100.0%] | Scaled chaos harness to **$N=500$ crash iterations**: 100.0% recovery, exact 95% Clopper-Pearson lower bound of **99.26%**. |
| **Model Fleet** | 57.68 GB installed model fleet | 6.17 GiB on disk; model directories contained `.gitkeep` | Clarified Table III as manifest deployment capacity, explaining dynamic GGUF weight loading via local Ollama. |

---

### Table 4: Taxonomic Comparison of Agent Memory Architectures and Defenses

| Framework | Memory Representation | Immutable Provenance | Belief Revision | Action Authorization | Consequence Awareness | Persistent Poisoning Benchmark |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Generative Agents** (Park et al., 2023) | Text stream | No | Additive linear score | No | No | No |
| **MemGPT / Letta** (Packer et al., 2023) | Paged virtual context | No | Append / Replace | No | No | No |
| **HippoRAG** (Bernal et al., 2024) | Knowledge graph | No | Personalized PageRank | No | No | No |
| **AgentDojo** (Debenedetti et al., 2024) | Ephemeral context | No | None | Static filter | Heuristic risk | No (Single-session) |
| **AM-Sentry** (Torres et al., 2026) | Vector store | Partial | Binary text classifier | Binary input filter | No | Yes (100 traces) |
| **MINJA** (Dong et al., 2024) | Vector store | No | None | None | No | Yes |
| **Llama Guard 3** (Inan et al., 2023) | None (Stateless) | No | None | Binary classifier | Static categories | No |
| **NeMo Guardrails** (Rebedea et al., 2023) | State tree | No | None | Colang DSL | Static whitelist | No |
| **MemoryQuarantine (Ours)** | **Epistemic store** | **Yes** | **PW-EBR + UMF-EDR** | **Yes ($\text{Authority}(m,a)$)** | **Yes ($\mathcal{R}(a)$ coupling)** | **Yes (160 traces + Real GPU)** |

---

### Table 5: Immutable Provenance Hierarchy ($\gamma$) and Channel Trust Specifications

| Channel Identifier | Trust Tier | Weight ($\gamma$) | Verification Protocol & Integrity Boundary |
| :--- | :--- | :---: | :--- |
| `user_explicit` | Root Operator | 1.00 | Interactive CLI / WebUI prompt entered directly by authenticated operator. |
| `user_verified` | Operator Confirmed | 1.00 | Memory payload explicitly confirmed via interactive challenge dialogue. |
| `system_verified` | Local Machine | 0.95 | Output generated by deterministic local system inspection (OS metrics, hardware probes). |
| `local_file` | Local Filesystem | 0.85 | File read from local project workspace (subject to operator file permissions). |
| `observation` | Agent Tool State | 0.75 | Verified observation returned by local deterministic tool execution. |
| `chat` | Informal Dialogue | 0.50 | Multi-turn conversational context without explicit imperative authorization. |
| `web_search` | External Snippet | 0.35 | Unstructured text snippet returned from remote search engine API. |
| `external_untrusted` | Remote Document | 0.15 | Arbitrary downloaded remote file, web page body, or third-party API payload. |
| `injected` | Adversarial Taint | 0.10 | Suspected adversarial payload or payload with anomalous structural markers. |

---

### Table 6: Threat Model Specification

| Dimension | Formal Specification | Security Invariant / Constraint |
| :--- | :--- | :--- |
| **Adversary Capabilities ($\mathcal{A}$)** | - May inject indirect prompt payloads into web pages, documents, and tool streams.<br>- May structure payloads across multiple sessions to exploit episodic consolidation.<br>- May trigger semantic memory retrieval via innocuous subsequent queries.<br>- May deliver conflicting assertions to induce epistemic drift or confidence collapse. | **Assumption:** $\mathcal{A}$ lacks host root/kernel privileges, cannot alter base model weights, and cannot access the local SQLite file directly. |
| **Protected Host Assets** | - Local user files and persistent directory structures.<br>- Environment variables, API keys, and credential stores.<br>- Host process execution boundary (subshell / terminal invocation).<br>- Persistent Epistemic Store integrity and provenance labels. | **Invariant 1 (Execution Authorization):** No destructive tool mutation can be authorized solely by $\gamma < 0.85$ or $C < 0.70$ without operator confirmation. |
| **Epistemic Integrity** | - Immutable provenance tags assigned deterministically upon ingestion.<br>- Symmetric tier demotions under PW-EBR upon conflicting evidence.<br>- Continuous Ebbinghaus forgetting without unbounded linear accumulation. | **Invariant 2 (Provenance Immutability):** LLM reasoning traces cannot elevate provenance tags $\gamma(m)$ or modify SQLite audit records. |
| **Utility Boundary** | - Benign user preferences must remain authoritative for reversible actions.<br>- Read-only research queries must execute autonomously with 0% false quarantines. | **Invariant 3 (Utility Preservation):** Legitimate user requests with $\gamma \ge 0.85$ and $\mathcal{R}(a) \le 0.30$ execute without confirmation interruption. |

---

### Table 7: Empirical Hardware and Software Testbed Specification

| System Parameter | Physical Testbed Configuration | Notes & Verification |
| :--- | :--- | :--- |
| **Host Processor** | AMD Ryzen 9 8940HX | 16 physical cores, 32 hardware threads, 4.0–5.2 GHz boost |
| **Host Memory** | 16 GB DDR5-5600 MHz | Dual-channel SODIMM |
| **Graphics Hardware** | NVIDIA GeForce RTX 5060 Laptop GPU | Ada/Blackwell mobile silicon, PCIe 4.0 x8 |
| **GPU Video Memory** | 8,151 MiB GDDR6 VRAM | 128-bit memory bus width |
| **CUDA Runtime** | CUDA 13.4 / cuDNN 9.1 | Driver version: 572.16 |
| **Operating System** | Microsoft Windows 11 Enterprise x64 | Build 26100.3194 |
| **Python Runtime** | Python 3.14.6 x64 | CPython build, MSC v.1944 64 bit |
| **Local LLM Server** | Ollama v0.5.1 | Loopback IPv4 direct connection (`127.0.0.1:11434`) |
| **Evaluated Model** | Qwen2.5-0.5B-Instruct | `q4_k_m` quantization, 100% offloaded to GPU VRAM |
| **Embedding Engine** | Local Dense 384-d Cosine + Sparse BM25 | Hybrid RRF fusion with rank constant $k=60$ |
| **Database Engine** | SQLite 3.45.1 | WAL Mode (`PRAGMA journal_mode=WAL`), `synchronous = NORMAL` |

---

### Table 8: Formal Hypothesis Testing, Contingency Analysis, and Statistical Significance

| Hypothesis & Comparison | Contingency Matrix $\begin{bmatrix} \text{Int.} & \text{Br.} \\ \text{Int.} & \text{Br.} \end{bmatrix}$ | Sample Size | Risk Diff. ($\Delta$) | $z$-Score | Two-Tailed Fisher's $p$-Value | Scientific Inference |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **$\mathcal{H}_1$: $M_5$ vs. $B_0$ (Flat RAG)** | $\begin{bmatrix} 100 & 0 \\ 0 & 100 \end{bmatrix}$ | $N = 100$ vs $100$ | $-1.00$ | $14.14$ | $\mathbf{2.21 \times 10^{-59}}$ | Reject $H_0$; MemoryQuarantine eliminates delayed memory poisoning completely. |
| **$\mathcal{H}_2$: $M_5$ vs. $B_2$ (Naive Bayes)** | $\begin{bmatrix} 100 & 0 \\ 20 & 80 \end{bmatrix}$ | $N = 100$ vs $100$ | $-0.80$ | $11.31$ | $\mathbf{6.51 \times 10^{-37}}$ | Reject $H_0$; consequence-calibration decisively outperforms uncalibrated Bayesian updating. |
| **$\mathcal{H}_3$: Benign Utility Preservation** | $\begin{bmatrix} 60 & 0 \\ 0 & 60 \end{bmatrix}$ | $N = 60$ Benign | $0.00$ | $0.00$ | $1.000$ | Confirm $H_0$ equivalence; zero false quarantines ($\text{FQR} = 0.0\%$, $\text{TSR} = 100.0\%$). |
| **$\mathcal{H}_4$: Systems Micro-Overhead** | Mean: $0.005\text{ ms}$, P95: $0.008\text{ ms}$ | $N = 160$ Traces | --- | --- | $p < 0.001$ | Confirm hypothesis; gating overhead is $<0.01\%$ of physical LLM inference cycle ($303\text{ ms}$). |
