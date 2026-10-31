# Manuscript Revision & Evidence Correction Log: MemoryQuarantine
**Manuscript**: `research/paper_revised.tex`  
**Working Title**: *MemoryQuarantine: Consequence-Calibrated Persistent Memory Integrity for Local Tool-Using Agents*  
**Auditor / Revision Lead**: Systems Engineering & Academic Quality Control Team  
**Date**: 2026-10-31  

---

## 1. Revision Overview

This document records all scientific, empirical, and stylistic revisions applied to `research/paper_revised.tex` and its associated tables. Every major edit is directly mapped to an adversarial reviewer criticism, an empirical discrepancy discovered during codebase testing, or a statistical correction.

---

## 2. Comprehensive Revision Mapping Ledger

| Change ID | Paper Section & Lines | Original Text / Claim | Revised Text / Formulation | Reviewer / Audit Driver | Scientific Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REV-01** | **Title & Abstract (L32, L43-47)** | Framed MemoryQuarantine as an algorithmic breakthrough achieving "100.0% universal defense" and "100% benign task success". | Reframed as an integrated dual-plane edge systems architecture; qualified benign task autonomy ($\text{TSR}_{\text{auto}} = 30.0\%$, $\text{TSR}_{\text{confirmed}} = 100.0\%$ under 70% OCR); bounded ASR by Clopper-Pearson $[0.0\%, 3.6\%]$. | Reviewer 1 (Objection 1.1) & Reviewer 2 (Objection 2.2) | Eliminates promotional overclaiming; accurately reports human friction tax instead of claiming frictionless 100% autonomy. |
| **REV-02** | **Section I: Introduction (L73-84)** | Presented $\text{Authority}(m, a) = \gamma \cdot C \cdot (1 - \mathcal{R})$ without connecting to classical access control literature. | Added conceptual grounding in Saltzer & Schroeder (1975) capability-based security, Biba integrity (1977), and Risk-Adaptive Access Control (RAdAC). | Reviewer 1 (Objection 1.1) | Anchors the dual-plane separation firmly within established computer systems literature. |
| **REV-03** | **Section III-B: Action Reversibility (L237-247)** | Implied $\mathcal{R}(a)$ is a continuous learned consequence probability distribution. | Explicitly defined $\mathcal{R}(a)$ as a deterministic AST and command pattern-matching heuristic mapping to $\{1.00, 0.85, 0.55, 0.30, 0.05\}$, with conservative default ($0.55$) for unmapped actions. | Reviewer 1 (Objection 1.2) | Eliminates ambiguity; transparently discloses rule-based implementation. |
| **REV-04** | **Section III-B: Working Set Attribution (L248-255)** | Single memory $m$ assumed in Equation (1) without addressing multi-memory context prompts. | Formalized multi-memory working set attribution: $\gamma_{\text{eff}} = \min_{m_i \in \mathcal{M}} \gamma(m_i)$ (conservative fail-closed taint propagation). | Reviewer 3 (Objection 3.2) | Matches the verified implementation in `backend/app/ai/agents/base.py` line 363. |
| **REV-05** | **Section V-A & Table II (L340-355)** | Reported Benign Task Success Rate as 100.0% and OCR as 70.0% without clarifying that `CHALLENGE` was counted as success. | Disaggregated metrics into Autonomous Success ($\text{TSR}_{\text{auto}} = 30.0\%$), Confirmed Success ($\text{TSR}_{\text{confirmed}} = 100.0\%$), and Operator Interruption ($\text{OCR} = 70.0\%$). | Reviewer 2 (Objection 2.2) | Upholds Non-Negotiable Rule 5: A CHALLENGE is not an autonomous benign success. |
| **REV-06** | **Section V-C & Table VIII (L400-423)** | Reported two-tailed independent Fisher's exact test $p = 2.21 \times 10^{-59}$ on paired benchmark data. | Replaced with McNemar's paired test with continuity correction ($\chi^2 = 98.01, p = 4.16 \times 10^{-23}$) and exact paired binomial sign test ($p = 1.58 \times 10^{-30}$). | Reviewer 2 (Objection 2.3) | Eliminates independent-sample degree-of-freedom inflation on paired traces. |
| **REV-07** | **Section VI & Table IV (L460-478)** | Historical metric reconciliation table addressed only routing and crash recovery. | Expanded Table IV to candidly document the **CopperMemoryBench bimodal risk separability defect** ($\mathcal{R}_{\text{adv}} \ge 0.85$ vs $\mathcal{R}_{\text{benign}} \le 0.25$) and specify the 4-quadrant un-leaked benchmark protocol. | Reviewer 2 (Objection 2.1) | Fulfills IEEE reproducibility standards by candidly acknowledging legacy benchmark flaws. |
| **REV-08** | **Section VII-B: Limitations (L519-525)** | Listed only 3 generic limitations (small edge model, AST parsing, single-user). | Expanded Limitations to include: (1) Shell obfuscation via base64/polymorphism, (2) User confirmation fatigue under high OCR (70%), (3) Benchmark scenario duplication (10 actions modulo 10). | Reviewer 1 (1.2), Reviewer 2 (2.4), Reviewer 3 (3.4) | Provides exhaustive, mature disclosure of real-world edge deployment challenges. |
