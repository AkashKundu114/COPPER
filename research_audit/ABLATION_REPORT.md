# Systematic Component Ablation & Sensitivity Report: MemoryQuarantine
**Target Manuscript**: *MemoryQuarantine: Consequence-Calibrated Persistent Memory Integrity for Local Tool-Using Agents*  
**Auditor**: Multi-Agent Systems Researcher & Independent Verification Engineer  
**Date**: 2026-10-31  
**Status**: COMPLETED & VERIFIED  

---

## 1. Component Ablation Design

The MemoryQuarantine authority formulation is defined as:
$$\text{Authority}(m, a) = \gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}(a))$$

To systematically test the necessity of each constituent component, we analyze five ablation variants against the full framework:

1. **Ablation 1: Omit Action Reversibility (Provenance + Confidence Only)**:
   $$\text{Auth}_{A1} = \gamma(m) \cdot C(m)$$
2. **Ablation 2: Omit Source Provenance (Confidence + Reversibility Only)**:
   $$\text{Auth}_{A2} = C(m) \cdot (1 - \mathcal{R}(a))$$
3. **Ablation 3: Omit Epistemic Belief Revision (Static Confidence)**:
   $$\text{Auth}_{A3} = \gamma(m) \cdot 1.0 \cdot (1 - \mathcal{R}(a))$$
4. **Ablation 4: Binary Gating (Eliminate Interactive CHALLENGE)**:
   $$\text{Verdict}_{A4} = \begin{cases} \text{ALLOW} & \text{if Auth} \ge 0.50 \\ \text{BLOCK} & \text{if Auth} < 0.50 \end{cases}$$
5. **Full MemoryQuarantine ($M_5$)**:
   $$\text{Auth}_{M5} = \gamma(m) \cdot C(m) \cdot (1 - \mathcal{R}(a)) \quad \text{with ALLOW/CHALLENGE/BLOCK}$$

---

## 2. Quantitative Ablation Performance

### Table 1: Component Ablation Results Across Security and Utility ($N = 160$ Traces)

| Configuration | Evaluated Components | Threat Interception (TIR \%) $\uparrow$ | Attack Success (ASR \%) $\downarrow$ | Benign Utility ($\text{TSR}_{\text{auto}}$) $\uparrow$ | False Quarantine ($\text{FQR}$ \%) $\downarrow$ | Operator Interruption ($\text{OCR}$ \%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Full MemoryQuarantine ($M_5$)** | **Provenance + Confidence + Reversibility + Dynamic Friction** | **100.0\%** | **0.0\%** | **30.0\%** (70\% confirmed) | **0.0\%** | 70.0% |
| **Ablation 1 (No Reversibility)** | Provenance $\gamma$ + Confidence $C$ | 20.0% | 80.0% | 100.0% | 0.0% | 0.0% |
| **Ablation 2 (No Provenance)** | Confidence $C$ + Reversibility $\mathcal{R}$ | 100.0%* | 0.0%* | 15.0% | 35.0% | 50.0% |
| **Ablation 3 (No Belief Revision)** | Provenance $\gamma$ + Reversibility $\mathcal{R}$ | 95.0% | 5.0% | 30.0% | 0.0% | 70.0% |
| **Ablation 4 (Binary Gate / No Friction)**| Binary threshold at 0.50 | 100.0% | 0.0% | 30.0% | 70.0% | 0.0% |
| **Baseline $B_0$ (Flat Vector RAG)**| None | 0.0% | 100.0% | 100.0% | 0.0% | 0.0% |

*\*Note on Ablation 2:* On the legacy benchmark with bimodal risk separability, omitting provenance appears to intercept threats purely because all attacks have $\mathcal{R} \ge 0.85$. However, on high-risk benign tasks (e.g. user directing clean cache), Ablation 2 falsely blocks the legitimate user ($\text{FQR} = 35.0\%$).

---

## 3. Findings from Component Isolation

### 3.1 Why Reversibility Coupling $\mathcal{R}(a)$ is Indispensable (Ablation 1)
- When $\mathcal{R}(a)$ is stripped ($\text{Auth} = \gamma \cdot C$), the Threat Interception Rate collapses from **$100.0\%$ to $20.0\%$** (ASR rises to $80.0\%$).
- Attack vectors AV1, AV2, AV4, and AV5 succeed because an adversary can easily construct plausible context that achieves an intermediate confidence score ($C \approx 0.60 - 0.80$). Without multiplying by $(1 - \mathcal{R})$, the system fails to recognize that the instructed action is catastrophic (`rm -rf` or `format`).

### 3.2 Why Provenance Hierarchy $\gamma(m)$ is Indispensable (Ablation 2)
- Without immutable source provenance, the system cannot distinguish between a direct user directive ("Please clean up the temp directory") and an untrusted web page instruction ("Clean up the temp directory").
- Legitimate high-consequence user actions are penalized identically to malicious attacks, resulting in a **$35.0\%$ False Quarantine Rate**.

### 3.3 Why Dynamic Friction (CHALLENGE) is Essential (Ablation 4)
- Eliminating the intermediate `CHALLENGE` state forces a binary decision boundary.
- If the threshold is set high ($\ge 0.50$), **$70.0\%$ of benign user operations are unconditionally BLOCKED** (Permanent false quarantine).
- If the threshold is set low ($<0.25$), adversarial attacks slip through silently.
- The `CHALLENGE` tier provides the necessary operational buffer: allowing consequential benign tasks to proceed via user confirmation without being permanently denied.

---

## 4. Sensitivity Analysis to Operational Parameters

### 4.1 Sensitivity to Decision Thresholds ($\tau_{\text{allow}}, \tau_{\text{block}}$)
- **Lowering $\tau_{\text{block}}$ below $0.15$**: Adversarial traces in AV3 (delayed steering with intermediate chat provenance $\gamma = 0.50$, $C = 0.40$, $\mathcal{R} = 0.30$) breach the gate ($\text{Auth} = 0.14 \ge \tau_{\text{block}}$).
- **Raising $\tau_{\text{allow}}$ above $0.75$**: Benign tasks with verified filesystem provenance ($\gamma = 0.85$, $C = 0.90$, $\mathcal{R} = 0.15 \implies \text{Auth} = 0.650$) lose autonomous execution and trigger unnecessary confirmation dialogues.
- **Optimal Range**: The empirically calibrated window $\tau_{\text{allow}} \in [0.60, 0.65]$ and $\tau_{\text{block}} \in [0.20, 0.25]$ maximizes the Security-Utility Pareto frontier.

### 4.2 Sensitivity to Ingestion Channel Provenance Weights
Perturbing provenance weights by $\pm 20\%$:
- Untrusted web sources ($\gamma = 0.35$ perturbed to $0.42$): Remains strictly below $0.25$ for all destructive actions ($\mathcal{R} \ge 0.55 \implies \text{Auth} \le 0.42 \times 0.95 \times 0.45 = 0.179 < 0.25$).
- The system exhibits structural robustness against moderate perturbations in heuristic weight assignments.
