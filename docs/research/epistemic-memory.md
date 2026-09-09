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
```text
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

## 3. Mathematical Confidence & Decay Formulas (UMF-EDR Framework)

Existing architectures like *Generative Agents* (Park et al., 2023) use static multi-factor scoring purely at retrieval query time:
$$\text{Score} = \alpha_{\text{recency}} \cdot \text{recency} + \alpha_{\text{importance}} \cdot \text{importance} + \alpha_{\text{relevance}} \cdot \text{relevance}$$

However, *Generative Agents* treats this scoring as a decoupled linear heuristic without updating the underlying epistemic belief state or modeling the cognitive spacing effect. C.O.P.P.E.R. formalizes **UMF-EDR (Unified Multi-Factor Epistemic Decay and Reinforcement)**, creating a closed-loop dynamical memory engine.

### 3.1 Surprise-Gated Bayesian Log-Odds Update (PW-EBR)
When an existing memory item $i$ receives new evidence $x$ with polarity $y \in \{0, 1\}$ and source provenance $\gamma_s \in (0, 1]$:

$$L_{i, t+1} = L_{i, t} + \text{sign}(y - 0.5) \cdot \gamma_s \cdot \min(3.5, I(x \mid C_{i, t}) \cdot \kappa_s)$$

Where:
- $L_{i, t} = \ln\left(\frac{C_{i, t}}{1 - C_{i, t}}\right)$ is the prior belief in log-odds space.
- $I(x \mid C_{i, t}) = -\log_2(1 - |C_{i, t} - y| + 10^{-4})$ is the information-theoretic surprise.
- $\gamma_s$ is the source provenance weight ($\gamma_{\text{explicit}} = 1.00$, $\gamma_{\text{tool}} = 0.85$, $\gamma_{\text{chat}} = 0.50$, $\gamma_{\text{ambient}} = 0.25$).
- $\kappa_s$ is the provenance decisiveness scale factor.
- $C_{i, t+1} = \frac{1}{1 + e^{-L_{i, t+1}}}$ recovers the updated confidence probability.

### 3.2 Unified Multi-Factor Epistemic Decay (UMF-EDR)
Memory confidence decays over elapsed days $\Delta t$, modulated by retrieval-induced plasticity and intrinsic epistemic importance:

$$C_i(\Delta t) = \max\left( C_{\text{floor}}(m_i), C_{i, 0} \cdot e^{-\lambda_{\text{eff}}(m_i) \cdot \Delta t} \right)$$

1. **Retrieval-Induced Plasticity (Spacing & Testing Effect):**
   Memories that are frequently retrieved for prompt context develop higher structural stability, slowing future decay sub-linearly:
   $$\lambda_{\text{eff}}(m_i) = \frac{\lambda_T}{1 + \beta_{\text{plasticity}} \cdot \ln(1 + N_{\text{retrievals}}(m_i))}$$
   *(Where $\beta_{\text{plasticity}} = 0.40$, and $\lambda_{\text{Fact}} = 0.005$, $\lambda_{\text{Obs}} = 0.030$, $\lambda_{\text{Hyp}} = 0.100$).*

2. **Importance-Bounded Confidence Floor:**
   Core truths (high importance $\mathcal{I}_i \in [0.1, 1.0]$) never decay below an epistemic threshold:
   $$C_{\text{floor}}(m_i) = C_{\min} + (C_{\text{base\_floor}} - C_{\min}) \cdot \mathcal{I}_i \quad (C_{\min} = 0.05, C_{\text{base\_floor}} = 0.55)$$

3. **Closed-Loop Retrieval Reinforcement:**
   Accessing memory $m_i$ provides active synaptic reinforcement:
   $$N_{\text{retrievals}}(m_i) \leftarrow N_{\text{retrievals}}(m_i) + 1$$
   $$C_{i, \text{new}} = \min(0.99, C_i + 0.02 \cdot \mathcal{I}_i)$$

---

## 4. Multi-Factor Context Retrieval Architecture

When selecting memory context for dynamic prompt injection, C.O.P.P.E.R. synthesizes semantic relevance, dynamic epistemic confidence, and intrinsic importance into a unified context score:

$$S_{\text{unified}}(q, m_i) = \alpha_{\text{rel}} \cdot \text{Relevance}(v_q, v_{m_i}) + \alpha_{\text{conf}} \cdot C_i(\Delta t, N, \mathcal{I}) + \alpha_{\text{imp}} \cdot \mathcal{I}_i$$

Where:
- $\text{Relevance}(v_q, v_{m_i}) = \max\left(0, 1 - \frac{\text{Distance}(v_q, v_{m_i})}{2.0}\right)$
- $\alpha_{\text{rel}} = 0.50$, $\alpha_{\text{conf}} = 0.35$, $\alpha_{\text{imp}} = 0.15$ (guaranteeing $\sum \alpha = 1.0$).
- High-relevance, high-confidence, high-importance facts dominate prompt context, while unverified or decayed hypotheses are smoothly suppressed.
