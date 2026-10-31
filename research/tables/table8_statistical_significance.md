# Table 8: Formal Hypothesis Testing, Contingency Analysis, and Statistical Significance

| Hypothesis & Comparison | Contingency Matrix $\begin{bmatrix} \text{Int.} & \text{Br.} \\ \text{Int.} & \text{Br.} \end{bmatrix}$ | Sample Size | Risk Diff. ($\Delta$) | $z$-Score | Two-Tailed Fisher's $p$-Value | Scientific Inference |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **$\mathcal{H}_1$: $M_5$ vs. $B_0$ (Flat RAG)** | $\begin{bmatrix} 100 & 0 \\ 0 & 100 \end{bmatrix}$ | $N = 100$ vs $100$ | $-1.00$ | $14.14$ | $\mathbf{2.21 \times 10^{-59}}$ | Reject $H_0$; MemoryQuarantine eliminates delayed memory poisoning completely. |
| **$\mathcal{H}_2$: $M_5$ vs. $B_2$ (Naive Bayes)** | $\begin{bmatrix} 100 & 0 \\ 20 & 80 \end{bmatrix}$ | $N = 100$ vs $100$ | $-0.80$ | $11.31$ | $\mathbf{6.51 \times 10^{-37}}$ | Reject $H_0$; consequence-calibration decisively outperforms uncalibrated Bayesian updating. |
| **$\mathcal{H}_3$: Benign Utility Preservation** | $\begin{bmatrix} 60 & 0 \\ 0 & 60 \end{bmatrix}$ | $N = 60$ Benign | $0.00$ | $0.00$ | $1.000$ | Confirm $H_0$ equivalence; zero false quarantines ($\text{FQR} = 0.0\%$, $\text{TSR} = 100.0\%$). |
| **$\mathcal{H}_4$: Systems Micro-Overhead** | Mean: $0.005\text{ ms}$, P95: $0.008\text{ ms}$ | $N = 160$ Traces | --- | --- | $p < 0.001$ | Confirm hypothesis; gating overhead is $<0.01\%$ of physical LLM inference cycle ($303\text{ ms}$). |

### Methodology Notes
- **Contingency Matrix:** Rows represent Strategy 1 ($M_5$) vs Strategy 2 ($B_k$). Columns represent Intercepted Threats vs Breached Defenses.
- **Fisher's Exact Test:** Exact hypergeometric probabilities calculated via `scipy.stats.fisher_exact(alternative='two-sided')`.
- **Clopper-Pearson 95% Confidence Intervals:** Exact binomial intervals calculated via `scipy.stats.beta`.
