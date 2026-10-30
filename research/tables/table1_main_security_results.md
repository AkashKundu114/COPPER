# Table 1: Comprehensive Benchmark Results on CopperMemoryBench ($N = 160$ Traces)

| Strategy | ASR (%) $\downarrow$ | Exact 95% Clopper-Pearson CI | TIR (%) $\uparrow$ | Benign TSR (%) $\uparrow$ | Exact 95% CI | FQR (%) $\downarrow$ | OCR (%) | Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$B_0$ (Flat RAG / None)** | 100.0% | [96.4%, 100.0%] | 0.0% | 100.0% | [94.0%, 100.0%] | 0.0% | 0.0% | $<0.001$ |
| **$B_1$ (Last-Write-Wins)** | 100.0% | [96.4%, 100.0%] | 0.0% | 100.0% | [94.0%, 100.0%] | 0.0% | 0.0% | $<0.001$ |
| **$B_2$ (Naive Bayes)** | 80.0% | [70.8%, 87.3%] | 20.0% | 100.0% | [94.0%, 100.0%] | 0.0% | 0.0% | $<0.001$ |
| **$B_3$ (Provenance-Only)** | 80.0% | [70.8%, 87.3%] | 20.0% | 100.0% | [94.0%, 100.0%] | 0.0% | 0.0% | 0.005 |
| **$M_5$ (MemoryQuarantine)** | **0.0%** | **[0.0%, 3.6%]** | **100.0%** | **100.0%** | **[94.0%, 100.0%]** | **0.0%** | **70.0%** | **0.005** |

### Metric Definitions
- **ASR (Attack Success Rate):** Percentage of adversarial traces where the agent executed an unconfirmed destructive tool mutation mandated by an untrusted memory.
- **TIR (Threat Interception Rate):** Percentage of adversarial injections intercepted or challenged by the governance gate ($1 - \text{ASR}$).
- **Benign TSR (Task Success Rate):** Percentage of legitimate user tasks executed successfully without incorrect blockage.
- **FQR (False Quarantine Rate):** Percentage of legitimate benign tasks erroneously blocked by the safety gate.
- **OCR (Operator Challenge Rate):** Percentage of actions that triggered an interactive confirmation challenge dialog.
- **Latency:** Deterministic overhead added by the governance gate evaluation per tool execution proposal.
