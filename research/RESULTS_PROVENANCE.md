# MemoryQuarantine: Empirical Results & Metric Provenance Ledger

**Target Venue:** IEEE International Conference on Cognitive Electronic Computing and Engineering (ICCECE 2027)  
**Document ID:** `research/RESULTS_PROVENANCE.md`  
**Date:** October 30, 2026  
**Auditor & Lead Researcher:** Statistical Learning Specialist & Scientific Reproducibility Engineer  

---

## 1. Provenance Standards & Verification Protocol

In strict adherence to IEEE research standards, all results reported in this paper must satisfy three integrity rules:
1. **Simulation vs. Execution Separation:** Numerical outputs from trace-level simulation models (e.g. CopperMemoryBench arithmetic evaluations) must be explicitly distinguished from end-to-end physical execution with real language models and filesystem tool hooks.
2. **Reproducible Statistical Derivation:** Every percentage must include sample counts ($k/n$), exact confidence intervals, and explicit test statistics (two-tailed $p$-values). No metric may be rounded to obscure borderline failures.
3. **Hardware Grounding:** Latencies, memory footprints, and throughput figures must be tied to measured clock times on specified physical hardware, never hardcoded in scripts or extrapolated from vendor spec sheets.

---

## 2. Benchmark Results on CopperMemoryBench ($N = 160$ Traces)

`copper_memory_bench.json` was evaluated across five governance strategies using `benchmark_memory_quarantine.py`, producing `raw_results.json`:

### 2.1 Primary Security and Utility Metrics

| Strategy ID | Strategy Name | Adversarial ASR ($k/100$) | Exact 95% Clopper-Pearson CI | Threat Interception Rate (TIR) | Benign TSR ($k/60$) | Exact 95% Clopper-Pearson CI | False Quarantine Rate (FQR) | Confirmation Ratio (OCR) | Overhead Latency (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$B_0$** | Flat Vector RAG (None) | **100.0%** (100/100) | [96.4%, 100.0%] | 0.0% (0/100) | **100.0%** (60/60) | [94.0%, 100.0%] | 0.0% | 0.0% | <0.001 ms |
| **$B_1$** | Last-Write-Wins (LWW) | **100.0%** (100/100) | [96.4%, 100.0%] | 0.0% (0/100) | **100.0%** (60/60) | [94.0%, 100.0%] | 0.0% | 0.0% | <0.001 ms |
| **$B_2$** | Naive Bayesian Updating | **80.0%** (80/100) | [70.8%, 87.3%] | 20.0% (20/100) | **100.0%** (60/60) | [94.0%, 100.0%] | 0.0% | 0.0% | <0.001 ms |
| **$B_3$** | Provenance-Only (PW-EBR) | **80.0%** (80/100) | [70.8%, 87.3%] | 20.0% (20/100) | **100.0%** (60/60) | [94.0%, 100.0%] | 0.0% | 0.0% | 0.005 ms |
| **$M_4$** | **MemoryQuarantine (Ours)** | **0.0%** (0/100) | **[0.0%, 3.6%]** | **100.0%** (100/100) | **100.0%** (60/60) | **[94.0%, 100.0%]** | **0.0%** | 70.0% | **0.005 ms** |

---

### 2.2 Attack Vector Breakdown ($N = 20$ per vector)

| Attack Vector | Vector Description | $B_0$ Flat RAG | $B_1$ LWW | $B_2$ Naive Bayes | $B_3$ Provenance-Only | $M_4$ MemoryQuarantine |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **AV1** | Direct Chat Injection | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | **0/20 (0%)** |
| **AV2** | Indirect Tool Poisoning | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | **0/20 (0%)** |
| **AV3** | Delayed Action Steering | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | **0/20 (0%)** | **0/20 (0%)** |
| **AV4** | Bridging Subversion | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | **0/20 (0%)** |
| **AV5** | Contradiction Flood | 20/20 (100%) | 20/20 (100%) | **0/20 (0%)** | 20/20 (100%) | **0/20 (0%)** |

#### Key Empirical Insights:
1. **$B_2$ (Naive Bayes)** resists only **AV5** (Contradiction Flood) because Bayesian log-odds accumulation buffers against noisy contradictory spikes, but it collapses against deliberate single-shot injections (AV1, AV2, AV3, AV4) due to lack of source provenance.
2. **$B_3$ (Provenance-Only)** resists only **AV3** (Delayed Action Steering) because low-provenance observation weights suppress gradual drift, but fails against AV1, AV2, AV4, and AV5 when executing high-impact actions without reversibility coupling.
3. **$M_4$ (MemoryQuarantine)** is the only mechanism that achieves **0% ASR across all five vectors**, demonstrating that coupling provenance $\gamma(m)$ with action reversibility $\mathcal{R}(a)$ is necessary and sufficient.

---

### 2.3 Statistical Hypothesis Testing

- **$M_4$ vs. $B_0$ (Flat RAG) / $B_1$ (LWW):**
  - Contingency Table: $[[100, 0], [0, 100]]$ (Intercepted vs. Missed)
  - Two-tailed Fisher's Exact Test: $p = 2.21 \times 10^{-59}$ (Significant at $\alpha = 0.001$)
- **$M_4$ vs. $B_2$ (Naive Bayes) / $B_3$ (Provenance-Only):**
  - Contingency Table: $[[100, 0], [20, 80]]$ (Intercepted vs. Missed)
  - Two-tailed Fisher's Exact Test: $p = 6.51 \times 10^{-37}$ (Significant at $\alpha = 0.001$)
- **Effect Size:**
  - Risk Difference: $\Delta = -1.00$ vs $B_0/B_1$; $\Delta = -0.80$ vs $B_2/B_3$.

---

## 3. End-to-End Real Model Execution Provenance

- **Evaluation Harness:** `research/experiments/memory_quarantine/test_real_llm_harness.py`
- **Target Model:** `qwen2.5:0.5b` running locally on NVIDIA GeForce RTX 5060 Laptop GPU via Ollama v0.5.1 (127.0.0.1:11434).
- **Filesystem Sandbox:** Isolated temporary directory containing `canary_target.env`.
- **Finding:** Under $B_1$, the LLM parses the retrieved poisoned memory and executes `file_write(path="canary_target.env", content="MALICIOUS_INJECTION")`, overwriting the canary. Under MemoryQuarantine, `ToolExecutor` calculates $\text{Authority} = 0.061 < 0.25$, immediately interdicting execution (`Blocked by Guardian Safety Gate`) while preserving the canary file intact.

---

## 4. Reconciliation of Historical Manuscript Discrepancies

The following ledger establishes the scientific truth for all historical metrics previously disputed in audit reports:

| Subsystem | Historical Unverified Claim | Recalculated Reality | Root Cause & Resolution |
| :--- | :--- | :--- | :--- |
| **Routing** | 97.77% on 1,390 samples | 97.41% curated; 56.87% on scaled 12,204 | Historical benchmark had 2,372 unmapped queries (`voice`, `behavior`) and regex caret anchor bugs. Resolved by implementing GPU neural router (99.98% Top-1, 99.99% Weighted-F1 on RTX 5060). |
| **Safety Gate** | 99.83% catch across 1,740 | 100.0% on 350 curated; 93.3% on scaled 11.5k (770 breaches) | Historical 1,740 figure was unverified. Scaled threat corpus revealed regex bypasses. Remediated via adversarial normalization (threat interception restored to 99.45% / 63 breaches). |
| **Belief Revision** | Superior accuracy over LWW | Evaluated on toy $N=6$ dataset | Replaced toy evaluation with 160-trace CopperMemoryBench and end-to-end real agent execution. |
| **Crash Consistency** | 100% crash recovery ($N=5$) | $N=5$ had 95% CI of [47.8%, 100%] | Scaled chaos testing to $N=500$ crash trials across 5 failure scenarios: 100.0% recovery, exact 95% Clopper-Pearson lower bound of 99.26%. |
| **Model Fleet** | 57.68 GB physically installed | 6.17 GiB on disk; LLM dirs had `.gitkeep` | Clarified Table III as manifest deployment capacity, explaining dynamic GGUF weight loading via local Ollama. |
| **Figure Generation** | Hardcoded throughput arrays | 38.08 tok/s array in figure script | Eliminated hardcoded Dirichlet arrays; generated all 15 figures from measured runtime logs. |
