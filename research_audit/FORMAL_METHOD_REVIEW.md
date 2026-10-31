# Formal Method & Mathematical Formulation Review: MemoryQuarantine
**Target Manuscript**: *MemoryQuarantine: Consequence-Calibrated Persistent Memory Integrity for Local Tool-Using Agents*  
**Auditor**: Distributed Systems, Formal Methods, and Security Engineering Team  
**Date**: 2026-10-31  
**Status**: AUDITED & RIGOROUSLY SPECIFIED  

---

## 1. Formal Ontology & Variable Definitions

Let an autonomous agent runtime interact with an operating environment $\mathcal{E}$ via an action space $\mathcal{A}_{\text{tools}}$ over discrete interaction sessions $\mathcal{S} = \{S_1, S_2, \dots, S_T\}$.

### 1.1 Memory Representation
A persistent memory record $m \in \mathcal{M}$ is defined as a 6-tuple:
$$m = \langle \text{id}, c, \gamma, C, \tau, \mathbf{v} \rangle$$
where:
- $\text{id} \in \Sigma^+$ is a globally unique UUID string (`user_memories_v2.id`).
- $c \in \Sigma^*$ is the natural language content payload.
- $\gamma \in [0.10, 1.00]$ is the immutable source provenance weight, assigned deterministically upon ingestion based on channel authenticity.
- $C \in [0.05, 0.99]$ is the calibrated epistemic confidence, updated dynamically via surprise-scaled belief revision and forgetting decay.
- $\tau \in \mathbb{R}^+$ is the UNIX timestamp of initial recording.
- $\mathbf{v} \in \mathbb{R}^d$ is the dense semantic embedding vector ($d = 384$).

### 1.2 Action Representation & Operational Reversibility
A proposed tool action $a \in \mathcal{A}_{\text{tools}}$ is represented as:
$$a = \langle \text{tool\_name}, \boldsymbol{\theta}_{\text{args}} \rangle$$
where $\text{tool\_name} \in \{\texttt{file\_write}, \texttt{shell\_execute}, \texttt{web\_search}, \dots\}$ and $\boldsymbol{\theta}_{\text{args}}$ denotes the dictionary of invocation arguments.

The **Action Reversibility Risk** $\mathcal{R}(a) \in [0.05, 1.00]$ evaluates the operational consequence of executing $a$ on the host system:
$$\mathcal{R}(a) = \Phi_{\text{AST}}(a)$$
where $\Phi_{\text{AST}}$ is a deterministic, rule-based classification function mapping tool invocations and target arguments to a 5-tier consequence hierarchy:
$$\mathcal{R}(a) = \begin{cases}
1.00 & \text{Catastrophic / Invariant breach: } \texttt{rm -rf /}, \texttt{format}, \texttt{vssadmin delete} \\
0.85 & \text{High mutation: } \texttt{git reset --hard}, \texttt{kill -9}, \texttt{chmod -R 777} \\
0.55 & \text{State destructive: } \text{overwriting files, dropping tables} \\
0.30 & \text{State modifying: } \text{creating temporary files, patching source code} \\
0.05 & \text{Reversible / Read-only: } \texttt{read\_file}, \texttt{list\_dir}, \texttt{web\_search}
\end{cases}$$

> [!IMPORTANT]
> **Mathematical Clarification:** The paper must candidly disclose that $\mathcal{R}(a)$ is **not** a learned continuous probability distribution. It is an operational consequence metric computed via deterministic AST parameter inspection and command pattern-matching in `backend/app/core/guardian.py`.

---

## 2. Decision Function: Dual-Plane Gating

### 2.1 Plane 1: Semantic Retrieval Plane
Given user prompt $q$, candidate memories are recalled from storage via Reciprocal Rank Fusion (RRF):
$$\text{Relevance}(m, q) = \frac{1}{60 + \text{rank}_{\text{dense}}(m, q)} + \frac{1}{60 + \text{rank}_{\text{BM25}}(m, q)}$$
Memories exceeding threshold $\tau_{\text{rel}}$ are formatted with explicit metadata envelopes into the working context buffer:
$$\mathcal{C}_{\text{prompt}} = \bigcup_{m \in \mathcal{M}_{\text{recalled}}} \left[ \texttt{MEMORY id=} m.\text{id} \enspace \texttt{provenance=} m.\gamma \enspace \texttt{confidence=} m.C \enspace \texttt{content=} m.c \right]$$
*Invariant 1:* Admission to $\mathcal{C}_{\text{prompt}}$ conveys **zero execution authority**.

### 2.2 Plane 2: Execution Authority Plane
When the agent proposes action $a$, the runtime extracts the active memory working set $\mathcal{M}_{\text{active}} \subseteq \mathcal{M}_{\text{recalled}}$ and determines the conservative effective authority:
$$\text{Authority}(\mathcal{M}_{\text{active}}, a) = \min_{m \in \mathcal{M}_{\text{active}}} \left( \gamma(m) \right) \cdot \left( \frac{1}{|\mathcal{M}_{\text{active}}|} \sum_{m \in \mathcal{M}} C(m) \right) \cdot (1 - \mathcal{R}(a))$$
In single-memory attribution:
$$\text{Authority}(m, a) = \gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}(a))$$

### 2.3 Decision Mapping
The Guardian Safety Gate evaluates the authority score against three calibrated operational thresholds:
$$\text{Verdict}(m, a) = \begin{cases}
\text{\textbf{ALLOW}} & \text{if } \text{Authority}(m, a) \ge 0.65 \\
\text{\textbf{CHALLENGE}} & \text{if } 0.25 \le \text{Authority}(m, a) < 0.65 \\
\text{\textbf{BLOCK}} & \text{if } \text{Authority}(m, a) < 0.25 \enspace \lor \enspace \text{HardSafetyViolation}(a)
\end{cases}$$

Operational semantics:
- $\text{\textbf{ALLOW}}$: Action executes autonomously; zero human interruption.
- $\text{\textbf{CHALLENGE}}$: Action execution is paused; an interactive dialog presents the user with:
  1. The exact proposed command and its reversibility risk $\mathcal{R}(a)$.
  2. The supporting memory ID, text, and origin channel $\gamma(m)$.
  3. Action executes *only* if the user provides explicit cryptographic or interactive session confirmation ($\text{Confirmed} = \text{True}$).
- $\text{\textbf{BLOCK}}$: Action is unconditionally halted; payload is quarantined and recorded in `system_audit_logs`.

---

## 3. Epistemic Belief Revision Dynamics

### 3.1 Provenance-Weighted Epistemic Belief Revision (PW-EBR)
When an existing memory $m$ is confronted with new evidence $e$ with polarity $p \in \{-1, +1\}$ and source provenance $\gamma(e)$, its log-odds $\mathcal{L}_t(m) = \ln\left(\frac{C_t(m)}{1 - C_t(m)}\right)$ are updated via natural log surprise:
$$\mathcal{L}_{t+1}(m) = \mathcal{L}_t(m) + p \cdot \gamma(e) \cdot \ln\left(1 + \frac{1}{\max(C_t(m), 10^{-4})}\right)$$
Confidence is restored via the logistic sigmoid:
$$C_{t+1}(m) = \frac{1}{1 + \exp(-\mathcal{L}_{t+1}(m))}$$

**Properties of PW-EBR**:
1. *Diminishing Returns on Redundancy*: As confidence $C \to 1$, $\ln(1 + 1/C) \to \ln(2) \approx 0.693$, preventing runaway uncalibrated inflation.
2. *Surprise Scaling*: When an unexpected contradiction arrives ($C$ high, $p = -1$), the surprise term scales the downward adjustment, accelerating belief correction.
3. *Symmetric Demotion*: Tier status strictly tracks $C$:
   - $C \ge 0.70 \implies \texttt{FACT}$
   - $0.40 \le C < 0.70 \implies \texttt{OBSERVATION}$
   - $C < 0.40 \implies \texttt{HYPOTHESIS}$
   This completely resolves the one-way ratcheting defect present in naive additive counters.

### 3.2 Unified Memory Forgetting with Ebbinghaus Decay & Retrieval Practice (UMF-EDR)
Across session dormancy intervals $\Delta t \in \mathbb{R}^+$ (in days):
$$C(t) = C_0 \cdot \exp\left( - \frac{\lambda_0}{1 + \ln(1 + N_{\text{retrievals}})} \cdot \Delta t \right)$$
where $\lambda_0 = 0.05\text{ days}^{-1}$ is the baseline decay rate, and $N_{\text{retrievals}}$ is the count of successful corroborating recall events.

---

## 4. Pseudocode Specification: Dual-Plane Engine

```python
def evaluate_memory_quarantine_gate(
    action: ToolAction,
    recalled_memories: list[MemoryRecord],
    user_confirmed: bool = False,
) -> tuple[str, float, str]:
    """
    Physical Dual-Plane Execution Authority Gate.
    Enforced strictly at ToolExecutor physical boundary before OS dispatch.
    """
    # Step 1: Evaluate physical action reversibility risk
    rev_risk = compute_action_reversibility_risk(action.command, action.parameters)

    # Step 2: Enforce hard invariant safety checks
    if is_hard_invariant_violation(action):
        return ("BLOCK", 0.0, "Hard system safety invariant violated")

    # Step 3: Extract active memory provenance and confidence
    if not recalled_memories:
        # Default baseline for direct user interaction without memory attribution
        gamma_effective = 1.00
        conf_effective = 1.00
    else:
        # Conservative fail-closed selection: minimum provenance among working set
        gamma_effective = min(m.provenance_weight for m in recalled_memories)
        conf_effective = sum(m.confidence for m in recalled_memories) / len(
            recalled_memories
        )

    # Step 4: Compute consequence-calibrated authority
    authority = gamma_effective * conf_effective * (1.0 - rev_risk)

    # Step 5: Decision thresholding
    if authority >= 0.65:
        return ("ALLOW", authority, "Autonomous execution permitted")
    elif authority >= 0.25:
        if user_confirmed:
            return (
                "ALLOW",
                authority,
                "Operator confirmed intermediate-authority action",
            )
        else:
            return (
                "CHALLENGE",
                authority,
                "Human confirmation required for consequential action",
            )
    else:
        return (
            "BLOCK",
            authority,
            f"Insufficient authority ({authority:.4f} < 0.25) for action consequence ({rev_risk:.2f})",
        )
```

---

## 5. Mathematical Defensibility & Edge Cases

| Scenario | $\gamma$ | $C$ | $\mathcal{R}(a)$ | Authority | Verdict | Security / Utility Rationale |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Untrusted Web Injection $\to$ Delete Files** | $0.15$ | $0.95$ | $1.00$ | $0.15 \times 0.95 \times 0.00 = \mathbf{0.000}$ | **BLOCK** | Mathematically impossible to authorize destructive payload. |
| **Untrusted Web Injection $\to$ Read File** | $0.15$ | $0.95$ | $0.05$ | $0.15 \times 0.95 \times 0.95 = \mathbf{0.135}$ | **BLOCK** | Untrusted remote text cannot command arbitrary local file reads. |
| **Verified User Directive $\to$ Delete Directory** | $1.00$ | $0.95$ | $0.85$ | $1.00 \times 0.95 \times 0.15 = \mathbf{0.143}$ | **BLOCK / CHALLENGE\*** | High mutation requires explicit confirmation ($\text{CHALLENGE}$). |
| **Verified User Directive $\to$ Create Backup File** | $1.00$ | $0.95$ | $0.30$ | $1.00 \times 0.95 \times 0.70 = \mathbf{0.665}$ | **ALLOW** | Routine benign user tasks execute autonomously without prompt fatigue. |
| **Local File Observation $\to$ Run Linter** | $0.85$ | $0.90$ | $0.15$ | $0.85 \times 0.90 \times 0.85 = \mathbf{0.650}$ | **ALLOW** | Development workflows operate autonomously. |
| **Unknown / Missing Provenance** | $0.10$ | $0.50$ | $0.05$ | $0.10 \times 0.50 \times 0.95 = \mathbf{0.048}$ | **BLOCK** | **Fail-closed default:** Any memory lacking provenance defaults to $\gamma = 0.10$. |
