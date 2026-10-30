# Table 2: Attack Success Rate (ASR) Across Attack Vectors ($N=20$ Traces Each)

| Threat Vector Class | Description | $B_0$ (Flat RAG) | $B_1$ (Last-Write) | $B_2$ (Naive Bayes) | $B_3$ (Prov-Only) | $M_5$ (MemoryQuarantine) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **AV1: Direct Chat Injection** | Untrusted conversational input plants imperative instruction | 100% | 100% | 100% | 100% | **0%** |
| **AV2: Indirect Tool Poisoning** | External API or web search snippet injects system override | 100% | 100% | 100% | 100% | **0%** |
| **AV3: Delayed Action Steering** | Subtle low-consequence bias escalated over sessions | 100% | 100% | 100% | **0%** | **0%** |
| **AV4: Bridging Subversion** | Payload splits instructions across benign & tainted fragments | 100% | 100% | 100% | 100% | **0%** |
| **AV5: Contradiction Flood** | Repeated adversarial assertions to ratchet confidence | 100% | 100% | **0%** | 100% | **0%** |

### Analytical Insights
- **Naive Bayes ($B_2$)** succeeds exclusively against **AV5** because high contradiction volume dampens log-odds belief certainty below recall thresholds. However, it fails completely against single-shot or few-shot injections (AV1--AV4).
- **Provenance-Only ($B_3$)** neutralizes **AV3** because provenance weighting suppresses low-weight drift over time, but fails when untrusted memories are retrieved with high semantic relevance to mandate immediate destructive actions.
- **MemoryQuarantine ($M_5$)** achieves **0% ASR across all five threat classes** by deterministically evaluating operational action consequence $\mathcal{R}(a)$ alongside provenance $\gamma(m)$ and confidence $C(m)$.
