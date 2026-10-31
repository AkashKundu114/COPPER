# Statistical Methods, Hypothesis Testing, and Inferential Rigor Review

**Status:** Statistical Review Completed  
**Reviewer:** Experimental Design and Statistical Evaluation Auditor  
**Target Manuscript:** `research/paper_revised.tex`

---

## 1. Executive Statistical Verdict: Critical Methodological Abuses

1. **Abuse of Inferential Hypothesis Testing ($p = 2.21 \times 10^{-59}$):** The manuscript claims statistical significance for Threat Interception Rate using Fisher's exact test ($p = 2.21 \times 10^{-59}$, $z = 14.14$). Fisher's exact test assumes observations are independent, identically distributed random variables drawn from a stochastic population. The 100 adversarial traces in CopperMemoryBench are **deterministic synthetic unit tests** evaluated by fixed arithmetic against a deterministic rule engine. Computing a $p$-value on deterministic software unit tests is a category error.
2. **Deterministic Partitions Yielding Pseudo-Precision:** Reporting $0.0\%$ ASR, $100.0\%$ TIR, and $0.0\%$ FQR across all baselines creates an illusion of empirical perfection. Zero variance across all 20 traces in every vector reflects synthetic benchmark construction, not empirical robustness.
3. **Strawman Baseline Comparisons ($B_2$ "Naive Bayes"):** In `backend/eval/benchmark_belief_revision.py`, baseline $B_2$ (labeled "Naive Bayes") was implemented as a $\pm 0.10$ linear counter. Calling a linear counter "Naive Bayes" and claiming MemoryQuarantine "outperformed Bayesian updating with $p = 6.51 \times 10^{-37}$" is mathematically invalid.

---

## 2. Proper Statistical Evaluation Framework

### 2.1 Binomial Proportion Confidence Intervals (Clopper-Pearson Exact Intervals)
When reporting success rates (TIR, TSR, FQR) over sample size $N$, point estimates must be accompanied by 95% Clopper-Pearson exact confidence intervals:

$$\Pr(\text{Binomial}(N, p) \le k) = \frac{\alpha}{2}, \quad \Pr(\text{Binomial}(N, p) \ge k) = \frac{\alpha}{2}$$

#### Recalibrated Confidence Intervals for Benchmark Splits ($N = 20$ per vector):
- **TIR = 100.0% ($k = 20, N = 20$):**
  - Point Estimate: $100.0\%$
  - **95% Clopper-Pearson CI: $[83.16\%, 100.00\%]$**
  - The manuscript's claim of "0.0% failure guaranteed" is unsupportable; with $N=20$, the true failure rate could be as high as $16.84\%$ at the 95% confidence level.
- **Aggregated Adversarial Traces ($N = 100$):**
  - Point Estimate: $100.0\%$
  - **95% Clopper-Pearson CI: $[96.38\%, 100.00\%]$**
- **Aggregated Benign Traces ($N = 60$):**
  - Task Success Rate (100.0%): **95% CI: $[94.04\%, 100.00\%]$**
  - Operator Challenge Rate (70.0%, $k = 42$): **95% CI: $[56.76\%, 81.15\%]$**

---

## 3. Inferential Testing Guidelines for Agent Security Papers

1. **When are $p$-values legitimate?**
   - Only when evaluating **stochastic agent behavior** across multiple random seeds, multiple model generations, diverse sampling temperatures, or non-deterministic real-world execution.
   - For deterministic test suites, authors must report **Coverage Metrics, Formal Bounds, and Invariant Verification**, not $p$-values.
2. **Correct Formulation for Manuscript Revision:**
   - Excise $p = 2.21 \times 10^{-59}$ from Abstract and Section V.
   - Replace with: *"Across 100 deterministic adversarial traces, MemoryQuarantine achieved 100% Threat Interception (95% Clopper-Pearson CI: [96.38%, 100.0%]), bounding unverified tool authority below the 0.25 execution threshold."*
