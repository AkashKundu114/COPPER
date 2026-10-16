# Epistemic Memory System Architecture

**Version**: `0.1.0-alpha`  
**Location**: `backend/app/memory/`  
**Test Suite**: `tests/memory/test_epistemic_thresholds.py`  

---

## 1. Executive Summary

C.O.P.P.E.R. implements an **Epistemic Decaying Memory Architecture**. Unlike conventional LLM memory systems that treat all context as flat, static text, C.O.P.P.E.R. models every belief with an epistemic confidence metric ($C \in [0.0, 1.0]$), an intrinsic importance value ($\mathcal{I} \in [0.0, 1.0]$), and an evidence provenance tier ($\gamma_s$).

Memories decay continuously over time unless reinforced through repeated user interaction or direct verification, preventing context poisoning and cognitive drift.

---

## 2. Epistemic Classification Thresholds

Beliefs are partitioned into three epistemic states based on confidence score $C$:

| Epistemic Tier | Confidence Range | Definition & Behavior | Handling in Context Retrieval |
| :--- | :--- | :--- | :--- |
| **FACT** | $C \ge 0.85$ | Ground truth explicitly confirmed by the user or verified by authoritative tool execution. | Injected into the core prompt context as immutable ground truth. |
| **OBSERVATION** | $0.50 \le C < 0.85$ | Corroborated interaction history or inferred behavioral preference. | Injected as situational context; open to user clarification or revision. |
| **HYPOTHESIS** | $C < 0.50$ | Preliminary deduction or unverified ambient observation. | Suppressed from immediate context injection; requires proactive confirmation before taking action. |

---

## 3. Mathematical Memory Dynamics

### 3.1 Unified Multi-Factor Decay
Memories decay exponentially as a function of elapsed time $t$, modulated by retrieval frequency $N$:

$$\lambda_{\text{eff}} = \frac{\lambda_0}{1 + \beta \cdot \ln(1 + N)}$$

$$C(t) = \max\left(C_{\text{floor}}, \, C_0 \cdot e^{-\lambda_{\text{eff}} \cdot t}\right)$$

Where:
- $\lambda_0$ is the base decay rate constant ($0.05 \text{ day}^{-1}$).
- $\beta$ is the retrieval reinforcement coefficient ($0.30$).
- $N$ is the number of times this memory was recalled and utilized.

### 3.2 Importance-Bounded Confidence Floor
High-importance memories (e.g., user allergies, security keys, primary project names) never completely decay:

$$C_{\text{floor}} = 0.05 + 0.50 \cdot \mathcal{I}$$

For an item with maximum importance ($\mathcal{I} = 1.0$), its confidence cannot drop below $0.55$, ensuring it remains at least an active `OBSERVATION`.

### 3.3 Evidence Provenance Weighting ($\gamma_s$)
When new evidence is absorbed, confidence updates are weighted by source trustworthiness:

| Provenance Source | Weight ($\gamma_s$) | Example Source |
| :--- | :--- | :--- |
| **User Explicit** | $1.00$ | "Always format python code with 4 spaces." |
| **Verified Tool Result** | $0.85$ | Direct exit code 0 output from a local AST inspection. |
| **Ambient Context** | $0.60$ | Inferred from recent file edits or window focus. |
| **Model Speculation** | $0.35$ | LLM-generated hypothetical deduction. |

---

## 4. Storage & Persistence

The memory engine combines relational and vector storage on the local filesystem:

1. **Relational Metadata (`data/copper.db` - SQLite via SQLAlchemy)**:
   - Stores memory IDs, raw text, epistemic confidence, importance, decay coefficients, and provenance.
   - Protected by Write-Ahead Logging (WAL) and automated crash recovery.
2. **Vector Embeddings (`data/chroma/` - ChromaDB)**:
   - Embeds memory text using local lightweight sentence embeddings for semantic retrieval.
   - Zero network egress; all embeddings generated locally on CPU.
3. **Knowledge Graph (`backend/app/knowledge_graph/`)**:
   - Maintains entity-relationship triples (Subject $\to$ Predicate $\to$ Object) with edge confidence scores.
