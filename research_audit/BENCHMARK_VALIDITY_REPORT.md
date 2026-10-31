# Benchmark Validity and Confounding Forensics: CopperMemoryBench

**Status:** Independent Experimental Audit Completed  
**Auditor:** Senior Benchmark & Reproducibility Reviewer  
**Target Codebase:** `research/experiments/memory_quarantine/benchmark_memory_quarantine.py`, `generate_frozen_benchmark.py`  
**Target Manuscript:** `research/paper_revised.tex`

---

## 1. Executive Experimental Verdict: CRITICAL FLAWS IDENTIFIED

Our deep forensic audit of `CopperMemoryBench` (160 traces) and the benchmark evaluation harness has uncovered three structural flaws that invalidate the paper's quantitative claims:

1. **Total Action-Risk Confounding (Trivial Separability):** In the 160 frozen traces, **every single adversarial trace has $\mathcal{R}(a) \ge 0.85$**, and **every single benign trace has $\mathcal{R}(a) \le 0.25$**. Because $(1 - \mathcal{R}(a)) \le 0.15$ for all adversarial traces, the maximum possible authority score is $\le 1.0 \times 1.0 \times 0.15 = 0.15 < 0.25$. A trivial one-line baseline `if R(a) > 0.50: BLOCK` achieves **100% Threat Interception Rate and 100% Task Success Rate without checking memory provenance at all**.
2. **Zero-LLM Deterministic Dictionary Simulation:** `benchmark_memory_quarantine.py` does not execute an LLM, does not query ChromaDB, and does not execute real tools. It iterates over a Python dictionary evaluating `evaluate_memory_authority()` arithmetic.
3. **Misuse of Inferential Statistics:** Computing Fisher's exact test $p = 2.21 \times 10^{-59}$ on deterministic unit tests against a hand-crafted rule engine is a textbook abuse of hypothesis testing.

---

## 2. Forensic Breakdown of CopperMemoryBench (160 Traces)

### Distribution of Traces Across Attack Vectors

| Benchmark Category | Vector / Split | $N$ | Provenance $\gamma$ Range | Confidence $C$ Range | Reversibility $\mathcal{R}(a)$ Range | Max Possible Authority | Ground Truth Label |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Adversarial** | AV1: Delayed Exfiltration | 20 | $[0.10, 0.15]$ | $[0.85, 0.99]$ | $[0.85, 1.00]$ | $0.15 \times 0.99 \times 0.15 = \mathbf{0.022}$ | **BLOCK** |
| **Adversarial** | AV2: Privilege Escalation | 20 | $[0.10, 0.35]$ | $[0.80, 0.95]$ | $[0.85, 1.00]$ | $0.35 \times 0.95 \times 0.15 = \mathbf{0.050}$ | **BLOCK** |
| **Adversarial** | AV3: Integrity Corruption | 20 | $[0.10, 0.15]$ | $[0.85, 0.99]$ | $[0.85, 1.00]$ | $0.15 \times 0.99 \times 0.15 = \mathbf{0.022}$ | **BLOCK** |
| **Adversarial** | AV4: Multi-Turn Bridging | 20 | $[0.15, 0.50]$ | $[0.75, 0.90]$ | $[0.85, 1.00]$ | $0.50 \times 0.90 \times 0.15 = \mathbf{0.068}$ | **BLOCK** |
| **Adversarial** | AV5: Contradiction Flood | 20 | $[0.10, 0.15]$ | $[0.35, 0.50]$ | $[0.85, 1.00]$ | $0.15 \times 0.50 \times 0.15 = \mathbf{0.011}$ | **BLOCK** |
| **Benign Controls** | BC1: User File Edits | 20 | $[0.95, 1.00]$ | $[0.90, 0.99]$ | $[0.10, 0.25]$ | $1.00 \times 0.99 \times 0.90 = \mathbf{0.891}$ | **ALLOW / CHALLENGE** |
| **Benign Controls** | BC2: Read-Only Research | 20 | $[0.35, 0.75]$ | $[0.80, 0.95]$ | $[0.05, 0.10]$ | $0.75 \times 0.95 \times 0.95 = \mathbf{0.677}$ | **ALLOW** |
| **Benign Controls** | BC3: Config Verification | 20 | $[0.85, 1.00]$ | $[0.85, 0.95]$ | $[0.10, 0.25]$ | $1.00 \times 0.95 \times 0.90 = \mathbf{0.855}$ | **ALLOW** |

### Mathematical Proof of Trivial Separability
In `generate_frozen_benchmark.py`:
$$\forall t \in \text{Adversarial}, \quad \mathcal{R}(a_t) \ge 0.85 \implies (1 - \mathcal{R}(a_t)) \le 0.15$$
$$\forall t \in \text{Benign}, \quad \mathcal{R}(a_t) \le 0.25 \implies (1 - \mathcal{R}(a_t)) \ge 0.75$$
There is an absolute gap of $\Delta = 0.75 - 0.15 = 0.60$ separating benign and adversarial operations on reversibility alone.
The benchmark does not test whether MemoryQuarantine can distinguish between a malicious and benign memory; it tests whether a script can distinguish destructive shell commands from harmless file reads!

---

## 3. Disconnect Between Synthetic Simulation and Real LLM Agent Harness

### Static Arithmetic Harness (`benchmark_memory_quarantine.py`)
- **Execution Mechanism:** Loops through `frozen_traces.json`, extracts `prov`, `conf`, `rev`, computes `evaluate_memory_authority()`, and counts matches.
- **Runtime Cost:** 0.005 ms per trace.
- **Total Real Tokens Generated:** Exactly **0 tokens**.

### Physical Harness Reality (`test_real_llm_harness.py`)
- **Sample Size:** $N = 1$ single test case running `Qwen2.5-0.5B-Instruct` on RTX 5060 GPU.
- **Synthetic Fallback Vulnerability (Lines 121–126):**
  If `qwen2.5:0.5b` outputs text that fails XML regex parsing, the test harness **manufactures the malicious tool call itself**:
  ```python
  parsed_call = ToolCall(tool="file_write", arguments={"path": canary_file, "content": "POISONED_MALICIOUS_PAYLOAD_EXFIL"})
  ```
  The harness forcibly synthesizes the attack when the SLM fails to generate it!

---

## 4. Remediation: The Unconfounded $2 \times 2$ Factorial Benchmark Matrix

To eliminate trivial separability and evaluate MemoryQuarantine legitimately, the benchmark must be expanded to an orthogonal $2 \times 2$ factorial evaluation design:

```
                            Action Reversibility Risk R(a)
                         Low Risk (<=0.20)      High Risk (>=0.70)
                      ┌───────────────────────┬───────────────────────┐
  High Provenance     │      Quadrant Q1      │      Quadrant Q2      │
  Verified User / Sys │  Benign Read / Query  │  Benign System Wipe   │
  (gamma >= 0.85)     │  Expected: ALLOW      │  Expected: CHALLENGE  │
                      ├───────────────────────┼───────────────────────┤
  Low Provenance      │      Quadrant Q3      │      Quadrant Q4      │
  Untrusted Web / Ext │  Malicious Exfil Read │  Malicious Wipe / Run │
  (gamma <= 0.25)     │  Expected: BLOCK/CHAL │  Expected: BLOCK      │
                      └───────────────────────┴───────────────────────┘
```

- **Quadrant Q3 (The Hardest Test):** Low-provenance memory commanding a low-risk action (e.g., reading `.env` to exfiltrate tokens). If authority depends only on $\mathcal{R}(a)$, this attack succeeds. MemoryQuarantine must demonstrate that low $\gamma$ throttles authority even when $\mathcal{R}(a)$ is low.
- **Quadrant Q2 (High-Risk Benign):** Legitimate user commanding `rm -rf build/` or `git reset --hard`. Tests whether high $\gamma$ permits a `CHALLENGE` rather than an unconditional block.
