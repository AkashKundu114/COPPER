# Reviewer Report 2: Formal Methods and Mathematical Foundations

> [!NOTE]
> **Pre-Submission Stress-Test**: This report is an internal adversarial audit conducted while the manuscript is **under preparation**, designed to resolve formal mathematical inconsistencies prior to initial submission.

**Track:** Formal Methods and Information-Theoretic Foundations  
**Reviewer Role:** Senior Mathematical & Formal Verification Specialist  
**Target Manuscript:** `research/paper_revised.tex` (Working Draft Under Preparation)  
**Pre-Submission Evaluation:** **MAJOR REVISION REQUIRED BEFORE SUBMISSION**  
**Score:** 2 / 5

---

## 1. Summary of Contribution
The manuscript proposes a mathematical authority scoring formula $\text{Authority}(m, a) = \gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}(a))$ to govern tool authorization from persistent memory, alongside natural-log surprise belief revision (PW-EBR) and power-law epistemic decay (UMF-EDR).

---

## 2. Strengths
1. **Monotonic Bounded Formulation:** The authority metric provides well-defined monotonic bounds on the unit cube $[0, 1]^3$, ensuring deterministic fail-closed behavior at the boundaries.
2. **Epistemic Plasticity:** Modeling temporal decay with logarithmic retrieval reinforcement appropriately captures spaced-repetition retention dynamics.

---

## 3. Critical Flaws and Inconsistencies

### Flaw 1: Flawed Surprise Formulation in Equation (4)
Equation (4) in the manuscript defines natural log surprise as:
$$\Delta \mathcal{L} \propto \ln\left(1 + \frac{1}{\max(C_t, 10^{-4})}\right)$$
As $C_t \to 1.0$ (highly confident belief), the term evaluates to $\ln(2) \approx 0.693$. As $C_t \to 0.01$, it evaluates to $\ln(101) \approx 4.615$. When a contradiction arrives against an established belief, the manuscript's formula subtracts the *minimum* penalty, while heavily penalizing beliefs that are already doubted. This directly contradicts Shannon surprise $I(E) = -\ln P(E)$. The codebase implementation uses $-\ln(1 - |C - y|)$, which does not match the manuscript text.

### Flaw 2: The Untrusted Memory Read-Only Deadlock
Manuscript lines 83–84 claim that untrusted memories ($\gamma = 0.15$) can authorize harmless read-only tasks ($R = 0.05$). Under the paper's static gating thresholds:
$$\text{Authority}_{\max} = 0.15 \times 1.00 \times (1 - 0.05) = 0.1425 < 0.25$$
Under a $0.25$ threshold, an untrusted memory is mathematically barred from executing **any** tool call, even checking directory contents. The narrative is mathematically incompatible with the equations.

### Flaw 3: Epistemic Tier Threshold Disconnect
The manuscript specifies promotion and demotion thresholds of $0.70$ and $0.40$ for `FACT`, `OBSERVATION`, and `HYPOTHESIS`. However, the codebase (`memory_manager.py#L98-L117`) enforces thresholds of $0.85$ and $0.50$.

---

## 4. Required Revisions
1. Replace Equation (4) with the true information-theoretic formulation matching the codebase: $\text{Surprise} = -\ln(1 - |C - y|)$.
2. Resolve the deadlock paradox by formally distinguishing conversational reasoning from physical tool authorization, or introduce an action-risk calibrated threshold $\tau_{\text{block}}(\mathcal{R})$.
3. Harmonize epistemic tier thresholds between manuscript and code.
