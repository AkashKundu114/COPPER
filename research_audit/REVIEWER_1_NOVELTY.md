# IEEE Peer Review Report — Reviewer 1: Novelty & Theory
**Manuscript**: *MemoryQuarantine: Consequence-Calibrated Persistent Memory Integrity for Local Tool-Using Agents*  
**Reviewer Identity**: Reviewer 1 (Hostile but Fair Expert in AI Systems, Agent Architectures, and Access Control)  
**Recommendation**: **MAJOR REVISION**  

---

## 1. Overall Impression
This paper addresses an increasingly critical problem in autonomous agent architectures: delayed indirect prompt injection via persistent memory systems. The authors argue that existing memory paradigms (MemGPT, Generative Agents, HippoRAG) conflate semantic retrieval relevance with tool execution authority. The proposed solution, "MemoryQuarantine", decouples retrieval from authority using a triple-product formula combining source provenance $\gamma$, epistemic confidence $C$, and action reversibility $(1 - \mathcal{R})$.

While the core conceptual observation—that memory security must be governed by operational action consequences rather than semantic text filtering—is insightful, the theoretical presentation suffers from noticeable overclaiming, mathematical imprecision, and blurred boundaries with classical access control.

---

## 2. Major Conceptual Objections

### Objection 1.1: The Algorithmic Novelty Question
Is MemoryQuarantine a genuinely new algorithm or an engineering synthesis of classical systems concepts?
- The provenance hierarchy $\gamma(m)$ is essentially classical Biba integrity / Clark-Wilson commercial integrity levels adapted to LLM memory channels.
- Epistemic confidence $C(m)$ uses standard log-odds belief updating with an ad-hoc "natural log surprise" factor.
- Action reversibility risk $\mathcal{R}(a)$ is a classical risk-adaptive access control (RAdAC) consequence score.
Multiplying three heuristic scalar numbers $\text{Auth} = \gamma \cdot C \cdot (1 - \mathcal{R})$ is a useful systems heuristic, but presenting this as a fundamental mathematical breakthrough overstates the theoretical contribution. The paper must position itself as an **integrated edge systems architecture**, not an entirely novel algorithmic paradigm.

### Objection 1.2: Heuristic Reversibility vs. Continuous Probability
Section III-B describes $\mathcal{R}(a)$ as if it were a smooth, mathematically calibrated probability distribution. In reality, Equation (5) is a piecewise lookup table mapping five discrete shell command classes to fixed numbers $\{1.00, 0.85, 0.55, 0.30, 0.05\}$.
- What happens if an action does not match these five categories?
- How does the system handle complex, polymorphic shell commands or chained commands (`cmd1 && cmd2`)?
- The paper must be honest: $\mathcal{R}(a)$ is evaluated via pattern-matching AST heuristics, not learned continuous inference.

### Objection 1.3: Epistemic Drift and Belief Convergence
Equation (2) introduces PW-EBR using natural log surprise. While the author claims this solves the "one-way ratcheting bug", there is no formal proof of convergence, stability, or boundedness under adversarial oscillation. If an adversary alternates between corroborating and contradictory statements across sessions, does the log-odds score exhibit limit cycles or chaotic volatility? A formal stability analysis is missing.

---

## 3. Detailed Technical Feedback

1. **Section I (Introduction, Line 68)**: The term *"The Retrieval-Authority Conflation Fallacy"* is well-coined and represents the strongest philosophical argument in the paper. However, the author should cite classic capability-based security (Saltzer & Schroeder, 1975) to anchor this concept in computer science literature.
2. **Equation (1) vs Equation (2)**: In Eq. (2), $\mathcal{L}(m)$ uses $\max(C_t(m), 10^{-4})$ to prevent division by zero. However, when $C_t(m) \to 1$, $\ln(1 + 1/C) \to \ln(2) \approx 0.693$. Explain why the surprise of a near-certain fact receiving corroboration is not zero, but bounded below by $\ln(2)$.
3. **Table II (Provenance Hierarchy)**: The channel weights (e.g., `web_search` = 0.35, `chat` = 0.50, `local_file` = 0.85) are assigned by hand. How sensitive is the system to these specific numbers? A sensitivity sweep across weight variations is required.

---

## 4. Required Revisions for Acceptance
- Rescale claims of "fundamental mathematical formulation" to "consequence-calibrated systems governance heuristic".
- Explicitly disclose the rule-based / AST nature of $\mathcal{R}(a)$ and state how unmapped commands are handled.
- Provide mathematical bounds or sensitivity analysis on PW-EBR under adversarial oscillation.
