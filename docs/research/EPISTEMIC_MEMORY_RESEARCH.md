# Epistemic Memory System Research & Model Specification

---

## 1. Abstract & Problem Statement

Traditional AI memory architectures store user information as static key-value pairs (e.g., `user_city = "New York"`). This approach suffers from two severe limitations:
1. **Lack of Certainty Grading:** Overhearing a single transient statement ("I might buy an iPad") is stored with the exact same weight as a lifelong truth ("I am allergic to peanuts").
2. **Memory Stagnation:** Outdated facts persist indefinitely without decaying over time or updating when contradictory evidence arrives.

C.O.P.P.E.R. solves this through an **Epistemic Memory Framework** based on Bayesian belief updates, confidence scoring, evidence counting, and temporal decay.

---

## 2. Epistemic Classification Hierarchy

![Epistemic Memory Architecture](../images/epistemic_memory_layers.png)
                            +-----------------------------------+
                            |    Raw Input Dialogue / Action    |
                            +-----------------+-----------------+
                                              |
                                              v
                            +-----------------------------------+
                            |  Heuristic / LLM Fact Extractor   |
                            +-----------------+-----------------+
                                              |
       +--------------------------------------+--------------------------------------+
       |                                      |                                      |
       v                                      v                                      v
+--------------+                       +--------------+                       +--------------+
|    FACT      |                       | OBSERVATION  |                       |  HYPOTHESIS  |
| Confidence   |                       | Confidence   |                       | Confidence   |
| 0.85 - 1.00  |                       | 0.50 - 0.84  |                       | 0.10 - 0.49  |
+--------------+                       +--------------+                       +--------------+
```

### 2.1 Epistemic Memory Types

1. **Facts ($C \ge 0.85$):** Explicitly verified statements or repeatedly confirmed user states (e.g., "User primary language is TypeScript"). High resistance to temporal decay.
2. **Observations ($0.50 \le C < 0.85$):** Contextual events or explicit user statements observed 1-2 times (e.g., "User worked on backend optimization on Tuesday night"). Moderate decay rate.
3. **Hypotheses ($0.10 \le C < 0.50$):** Pattern inferences deduced by the Epistemic Learner (e.g., "User may prefer dark-themed dashboards over light-themed"). Higher decay rate; requires reinforcement to transition to an Observation.

---

## 3. Mathematical Confidence & Decay Formulas

### 3.1 Reinforcement Formula (Bayesian Update)
When an existing memory item $i$ is re-observed or reinforced, its confidence score $C_i$ is updated via:

$$C_{i, \text{new}} = C_{i, \text{old}} + (1 - C_{i, \text{old}}) \times \alpha \times \log_2(1 + E_i)$$

Where:
- $C_{i, \text{old}}$ is the current confidence score.
- $\alpha$ is the learning rate hyperparameter ($\alpha = 0.15$).
- $E_i$ is the cumulative evidence count ($E_{i, \text{new}} = E_{i, \text{old}} + 1$).

### 3.2 Temporal Decay Formula
Confidence decays gradually over time unless reinforced:

$$C_i(t) = C_{i, 0} \times e^{-\lambda_T \cdot \Delta t}$$

Where:
- $\Delta t$ is the time elapsed in days since last reinforcement.
- $\lambda_T$ is the decay constant specific to epistemic type $T$:
  - $\lambda_{\text{Fact}} = 0.005\text{ days}^{-1}$ (Half-life $\approx 138\text{ days}$)
  - $\lambda_{\text{Observation}} = 0.03\text{ days}^{-1}$ (Half-life $\approx 23\text{ days}$)
  - $\lambda_{\text{Hypothesis}} = 0.10\text{ days}^{-1}$ (Half-life $\approx 7\text{ days}$)

---

## 4. Hybrid Retrieval Architecture (Vector + Relational)

When retrieving memory context for prompt augmentation:
1. **Relational Query:** Selects top high-confidence Facts ($C \ge 0.85$) belonging to the active user context.
2. **Vector Similarity Query (ChromaDB):** Performs cosine similarity search over `copper_epistemic_memory` collection using query embedding $v_q$.
3. **Combined Rank Score:**

$$S_{\text{final}} = w_v \cdot \text{CosineSim}(v_q, v_m) + w_c \cdot C_m$$

Where $w_v = 0.6$ and $w_c = 0.4$. This ensures that relevant observations with high confidence score higher than low-confidence semantic matches.
