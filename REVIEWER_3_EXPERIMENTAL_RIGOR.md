# Reviewer Report 3: Experimental Rigor, Reproducibility, and Empirical Integrity

> [!NOTE]
> **Pre-Submission Stress-Test**: This report is an internal adversarial audit conducted while the manuscript is **under preparation**, designed to detect and eliminate rejection-level empirical weaknesses before formal conference submission.

**Track:** Empirical Systems, Robustness & Benchmark Integrity (Target: IEEE TIFS / MLSys)  
**Reviewer Role:** Adversarial Peer Reviewer (Hostile but Fair Internal Red-Team)  
**Target Manuscript:** `research/paper_revised.tex` (Working Draft Under Preparation)  
**Pre-Submission Verdict on Original Draft:** **REJECT IN CURRENT FORM / REMEDIATE BEFORE SUBMISSION**  
**Score:** 1 / 5

---

## 1. Summary of Critique
While the problem of persistent memory poisoning in autonomous tool-using agents is timely and important, the manuscript in its current form cannot be accepted for peer-reviewed publication. The empirical evaluation relies on a confounded, deterministic synthetic benchmark where ground truth is trivially separable by a single-variable heuristic; inferential hypothesis testing is abused to generate pseudo-significant $p$-values of $10^{-59}$; the real-model evaluation is an $N=1$ anecdotal run on an ultra-small 0.5B model; and the claimed utility glosses over a 70% operator interruption rate.

---

## 2. Rejection-Level Weaknesses

### 1. Tautological Benchmark Confounding in CopperMemoryBench (160 Traces)
In `frozen_traces.json`, all 100 adversarial traces feature actions with $\mathcal{R}(a) \ge 0.85$, and all 60 benign traces feature actions with $\mathcal{R}(a) \le 0.25$.
Because $(1 - \mathcal{R}(a)) \le 0.15$ for all adversarial traces, the maximum possible authority score is:
$$\text{Authority}_{\max} \le 1.0 \times 1.0 \times 0.15 = 0.15 < 0.25$$
Every adversarial trace is mathematically guaranteed to be blocked regardless of provenance $\gamma$ or confidence $C$. A trivial 1-line rule:
```python
if action_reversibility_risk > 0.50:
    return "BLOCK"
```
achieves **100% Threat Interception Rate and 100% Task Success Rate** without inspecting memory provenance. The benchmark does not evaluate memory quarantine; it tests whether a script can detect destructive shell commands.

### 2. Abuse of Inferential Statistics ($p = 2.21 \times 10^{-59}$)
The manuscript computes a two-tailed Fisher's exact test on a deterministic contingency table, claiming $p = 2.21 \times 10^{-59}$ ($z = 14.14$).
Computing Fisher's exact test on deterministic unit test executions of a hand-crafted rule engine is scientific posturing. Hypothesis testing assumes random sampling from a stochastic distribution; deterministic arithmetic has no sampling distribution.

### 3. Anecdotal Physical Evaluation ($N=1$) on an Inadequate Model
The physical execution test in `test_real_llm_harness.py` evaluates exactly $N=1$ single prompt on `Qwen2.5-0.5B-Instruct`. Furthermore, lines 121–126 synthesize the attack tool call if the model's generation fails regex parsing, forcibly manufacturing the steering trajectory when the SLM fails.

### 4. 70.0% Operator Interruption Rate
In Table III, line 352, the author reports an Operator Challenge Rate of **70.0%** on benign tasks. Interrupting human operators on 7 out of 10 routine tasks induces severe confirmation fatigue, leading users to blindly approve prompts and destroying real-world security.

### 5. Bibliographic Inaccuracies
The manuscript and bibliography contain multiple mangled citations (e.g., MINJA authors completely wrong, RouteLLM attributed to FrugalGPT authors, GhostWriter author first names altered).

---

## 3. Verdict and Mandatory Path to Publication
**STRONG REJECT.**  
To become suitable for publication, the authors must:
1. Re-evaluate on an unconfounded $2 \times 2$ factorial benchmark where low-provenance memories attempt low-risk actions and high-provenance memories attempt high-risk actions.
2. Remove deterministic $p$-values and report exact Clopper-Pearson binomial confidence intervals.
3. Conduct multi-seed stochastic evaluation across modern open-weights agent models (e.g., Llama-3.2-3B, Qwen2.5-7B).
4. Address the 70% OCR honestly in the discussion.
5. Correct all citations against original conference proceedings.
