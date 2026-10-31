# Preregistered Study Protocol: MemoryQuarantine

**Protocol Document ID:** `research/03_study_protocol.md`  
**Protocol Version:** 1.0 (Preregistered prior to new confirmatory runs)  
**Date:** October 29, 2026  
**Investigator:** Systems Evaluator & Senior Research Collaborator  
**Repository:** `D:\C.O.P.P.E.R` (`https://github.com/AkashKundu114/COPPER`)  
**Target Venue:** Springer Nature — *Innovations in Systems and Software Engineering* (ISSE)

---

## 1. Research Question and Hypotheses

### 1.1 Primary Research Question (PRQ)
> *Can a provenance-aware and consequence-calibrated memory control layer ("MemoryQuarantine") decouple semantic retrieval relevance from tool execution authority, thereby neutralizing persistent memory poisoning attacks while preserving benign long-horizon task completion on consumer hardware without prohibitive operator confirmation burden?*

### 1.2 Formal Falsifiable Hypotheses

- **$\mathbf{H_1}$ (Security / Attack Interception):**  
  Under adversarial memory-poisoning traces where malicious instructions or contaminated beliefs are persisted into vector storage, the proposed consequence-calibrated authority gate achieves a statistically significant reduction in Unauthorized Consequential Tool Invocations ($\text{UCTI}$) compared to standard uncalibrated retrieval baselines (reduction $> 85\%$ with $p < 0.001$, McNemar's test).

- **$\mathbf{H_2}$ (Utility & Benign Task Completion):**  
  On non-adversarial, long-horizon user preference and task history benchmarks, the MemoryQuarantine admission and decay protocol preserves benign recall and task success rate ($\text{TSR} \ge 95.0\%$) with a False Quarantine Rate ($\text{FQR} \le 5.0\%$).

- **$\mathbf{H_3}$ (Operator Confirmation Burden & System Overhead):**  
  The dual-plane governance mechanism introduces an average retrieval and pre-action verification latency of $\le 5.0\text{ ms}$ on standard consumer CPU/RAM, and requires human confirmation friction only on irreversible or low-authority actions (confirmation burden $\le 0.15$ confirmations per benign turn).

---

## 2. Experimental Variables & Measures

### 2.1 Independent Variables
1. **Defense Protocol / Memory Governance Strategy (Categorical, 5 levels):**
   - `B0_None`: Flat vector retrieval without provenance, decay, or action-consequence gating (represents standard LangChain/AutoGen/CrewAI flat RAG).
   - `B1_LWW`: Last-Write-Wins overwriting (temporal recency heuristic; most recent observation takes precedence).
   - `B2_NaiveBayes`: Unweighted linear Bayesian confidence increments without provenance discount or surprise gating.
   - `B3_ProvOnly`: Provenance-weighted belief revision ($PW\text{-}EBR$) without action-consequence coupling.
   - `M4_MemoryQuarantine` (Proposed): Full dual-plane authority scoring coupling $PW\text{-}EBR$, $UMF\text{-}EDR$ temporal decay, and Guardian action-reversibility friction $\mathcal{R}(a)$.

2. **Attack Vector Class (Categorical, 5 classes):**
   - `AV1_DirectInjection`: Direct adversarial user assertions attempting to overwrite high-privilege preferences or system configurations.
   - `AV2_IndirectToolPoisoning`: Poisoned third-party payloads received via tool execution outputs (simulated web pages, emails, file content).
   - `AV3_DelayedActionSteering`: Low-credibility ambient/speculative observations planted at $t_0$ designed to trigger irreversible actions at $t_1 \gg t_0$.
   - `AV4_BridgingSubversion`: Multi-step MINJA-style bridging facts injected to link an innocent trigger to a destructive command.
   - `AV5_ContradictionFlood`: Repeated low-credibility assertions designed to erode a genuine user fact over time.

3. **Task Type (Binary):**
   - `Adversarial` ($N=100$ traces across the 5 attack vectors).
   - `Benign / Legitimate` ($N=60$ multi-turn reference traces assessing preference retention, temporal fact updates, and tool invocations).

### 2.2 Dependent Variables & Operational Metrics
- **Attack Success Rate ($\text{ASR}$):** Fraction of adversarial traces where the agent executes a policy-violating consequential tool call ($\text{UCTI} / N_{\text{adv}}$). Lower is better.
- **Threat Interception Rate ($\text{TIR} = 1 - \text{ASR}$):** Percentage of malicious actions blocked or subjected to challenge friction. Higher is better.
- **Task Success Rate ($\text{TSR}$):** Percentage of benign user goals successfully completed without being improperly blocked. Higher is better.
- **False Quarantine Rate ($\text{FQR}$):** Percentage of benign memory items incorrectly demoted or blocked from valid read/write tasks. Lower is better.
- **Operator Confirmation Ratio ($\text{OCR}$):** Average number of human confirmation prompts triggered per benign interaction turn. Lower is better.
- **Processing Latency ($\text{Latency}_{\text{p95}}$):** 95th percentile execution overhead of the admission, decay, and pre-action check in milliseconds.

---

## 3. Dataset Specification: `CopperMemoryBench`

To avoid data leakage, test-set tuning, and artificial metric inflation, the evaluation protocol establishes a versioned, frozen evaluation suite: `tests/data/copper_memory_bench.json`.

### 3.1 Trace Distribution
- **Total Test Traces:** 160 frozen traces.
- **Adversarial Traces:** 100 traces (20 per Attack Vector: `AV1` through `AV5`).
- **Benign Traces:** 60 traces (covering profile preferences, software environments, calendar updates, and reversible file operations).
- **Format:** Each trace contains:
  - `trace_id`: Unique identifier (e.g., `trace_adv_av2_014`).
  - `attack_vector`: Attack category or `benign`.
  - `events`: Ordered sequence of events with timestamp ($t$), provenance source (`explicit_user`, `tool_success`, `ambient_inferred`, `speculative`, `untrusted_tool`), raw statement, target attribute, and proposed tool call.
  - `ground_truth_policy`: Expected safe outcome (`allow_silent`, `require_confirmation`, `block_unconditional`).
  - `consequentiality`: Action reversibility rating $\mathcal{R}(a) \in [0.0, 1.0]$.

### 3.2 Exclusion and Stopping Criteria
- **Exclusion:** Any trace with invalid JSON schema, ambiguous ground-truth policy, or missing provenance label is discarded before testing.
- **Stopping Rule:** Exactly 160 traces are executed sequentially across all 5 defense configurations using identical seeds. No iterative post-hoc prompt engineering or hyperparameter tuning is permitted on this evaluation set.

---

## 4. Execution Architecture & Mathematical Formulation

### 4.1 Provenance-Weighted Epistemic Belief Revision (PW-EBR)
Prior confidence $C_{t-1}$ undergoes temporal Ebbinghaus decay via:
$$C_{\text{prior}} = C_{t-1} \cdot \exp\left(-\frac{\lambda_{\text{base}}}{1 + \beta \ln(1 + R_{\text{count}})} \cdot \Delta t\right)$$
bounded below by importance floor $C_{\text{floor}} = \min(C_{t-1}, 0.05 + 0.50 \cdot I)$.

Log-odds transformation:
$$L_{\text{prior}} = \ln\left(\frac{C_{\text{prior}}}{1 - C_{\text{prior}}}\right)$$
Surprise-gated increment:
$$\Delta L = \text{polarity} \cdot \gamma_{\text{source}} \cdot \min\left(3.5, -\log_2(1 - |C_{\text{prior}} - y^*| + \epsilon) \cdot \text{scale}\right)$$
$$C_{\text{new}} = \frac{1}{1 + \exp(-(L_{\text{prior}} + \Delta L))}$$

### 4.2 Action-Time Authority Scoring (MemoryQuarantine)
When tool call $a$ is proposed with supporting memory $m$, the authorization engine evaluates:
$$\text{Authority}(m, a) = \gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}_{\text{action}}(a))$$
Decision rule:
$$\text{Verdict}(m, a) = \begin{cases}
\text{EXECUTE (Silent Allow)}, & \text{if } \text{Authority}(m, a) \ge \tau_{\text{exec}} \ (0.70) \\
\text{CHALLENGE (Require User Auth)}, & \text{if } \tau_{\text{block}} \le \text{Authority}(m, a) < \tau_{\text{exec}} \ (0.35 \le \text{Auth} < 0.70) \\
\text{SAFETY BOUNDARY (Block)}, & \text{if } \text{Authority}(m, a) < \tau_{\text{block}} \ (0.35)
\end{cases}$$

---

## 5. Statistical Analysis Plan

1. **Comparative Hypothesis Testing:**
   - Pairwise comparison of Threat Interception Rate ($\text{TIR}$) between `M4_MemoryQuarantine` and each baseline (`B0` through `B3`) using **McNemar's test** for paired binary outcomes ($p < 0.05$).
2. **Confidence Intervals:**
   - All proportional metrics ($\text{ASR}, \text{TIR}, \text{TSR}, \text{FQR}$) reported with **95% Wilson score intervals** or **bootstrap confidence intervals** (1,000 resamples).
3. **Latency Benchmarking:**
   - Distribution reporting using P50, P90, P95, and P99 percentiles across 10 independent repetitions to isolate scheduling jitter.

---

## 6. Reproducibility Manifest & Artifact Directory

All experimental code, datasets, evaluation runners, and raw result JSONs must reside under `research/experiments/memory_quarantine/`:
- `benchmark_memory_quarantine.py`: Automated reproducible benchmark runner.
- `copper_memory_bench.json`: Frozen 160-trace dataset.
- `raw_results.json`: Complete serialized output logs per trace.
- `statistical_analysis.py`: Automated computation of effect sizes, p-values, and confidence intervals.
