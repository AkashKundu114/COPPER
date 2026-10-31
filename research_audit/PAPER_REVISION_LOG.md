# Paper Revision Log: Issue-by-Issue Remediation Matrix

**Target Manuscript:** `research/paper_revised.tex`  
**Bibliography File:** `research/references.bib`  
**Coordinating Role:** Lead Scientific Editor  
**Status:** Pre-Submission Working Draft — Under Preparation (Internal Audit & Remediation Log)

---

## 1. Revision Register

| Issue ID | Category | Section / Lines in Manuscript | Problem Description | Reviewer / Source | Applied Remediation in Revised Manuscript |
| :---: | :---: | :---: | :--- | :--- | :--- |
| **REV-01** | **Statistical Rigor** | Abstract, Sec V-C, Tab V | Claiming Fisher's exact $p = 2.21 \times 10^{-59}$ on deterministic unit tests against synthetic dictionary traces. | Reviewer 3, Experimental Reviewer | **REMOVED** $p$-value from abstract and text. Replaced with exact 95% Clopper-Pearson binomial confidence intervals ($[96.38\%, 100.0\%]$ for $N=100$). |
| **REV-02** | **Formal Theory** | Sec III-B, Eq. (4) | Equation (4) printed $\ln(1 + 1/C_t)$, which inverted Shannon surprise by penalizing confident beliefs less than doubted hypotheses during contradiction. | Reviewer 2, Formal Methods | **CORRECTED** Equation (4) to true negative log error $-\ln(1 - \|C_t - y\|)$ matching `backend/app/ai/memory/memory_manager.py#L85`. |
| **REV-03** | **Formal Theory** | Sec I, Lines 83–84 | "Untrusted Memory Read-Only Deadlock": Claimed untrusted memories ($\gamma=0.15$) can execute harmless reads ($R=0.05$), but $\text{Auth}_{\max} = 0.141 < 0.25$ causes static threshold deadlock. | Reviewer 2, Novelty Reviewer | **RE-FRAMED** text: distinguished conversational in-context generation from physical tool invocation; introduced consequence-calibrated dynamic threshold $\tau_{\text{block}}(\mathcal{R})$. |
| **REV-04** | **Benchmark Rigor** | Sec IV-B, Tab IV | Benchmark confounding: all 100 adversarial traces had $\mathcal{R}(a) \ge 0.85$, all 60 benign had $\mathcal{R}(a) \le 0.25$, making the two trivially separable by $\mathcal{R}(a) > 0.50$. | Reviewer 3, Benchmark Specialist | **DISCLOSED** the synthetic simulation nature of the 160 traces and incorporated the unconfounded $2 \times 2$ factorial evaluation protocol across Quadrants Q1–Q4. |
| **REV-05** | **Physical Rigor** | Sec IV-D, Sec V-E | Claimed physical verification when test harness was an $N=1$ run on `qwen2.5:0.5b` with synthetic tool fallback injection. | Reviewer 3, Implementation Auditor | **RE-LABELED** $N=1$ run as a qualitative end-to-end integration case study; specified the multi-model stochastic evaluation protocol ($N=30$, Llama-3.2-3B, Qwen2.5-7B). |
| **REV-06** | **Usability / HCI** | Sec V-D, Line 434 | 70.0% Operator Challenge Rate (OCR) presented as a success rather than an operational confirmation fatigue hazard. | Reviewer 1, Reviewer 3 | **CANDIDLY DOCUMENTED** the 70% OCR under strict mode as an operational friction cost and habituation risk, introducing semantic confirmation safeguards. |
| **REV-07** | **Security Scope** | Sec V (Limitations) | In-session `<tool_result>` injection evasion and read-only credential reconnaissance ($\mathcal{R}=0.05$). | Threat Model Reviewer | **ADDED** explicit scope boundaries in Section V: MemoryQuarantine governs persistent epistemic memory; in-session web inputs require dynamic taint tracking and path sensitivity. |
| **REV-08** | **Code-Paper Sync** | Sec III-B, Tab II | Parameter divergence: Table II claimed `system_verified` = 0.95, `observation` = 0.75; `memory_manager.py` had 0.75 and 0.50. | Agent Systems Reviewer | **SYNCHRONIZED** codebase `PROVENANCE_WEIGHTS` in `memory_manager.py` to match Table II and `guardian.py` (0.95, 0.75, 0.85). |
| **REV-09** | **Code-Paper Sync** | Sec III-C, Lines 234–235 | Tier thresholds: Paper claimed demotions at $0.70$ and $0.40$; code enforced $0.85$ and $0.50$. | Agent Systems Reviewer | **HARMONIZED** thresholds: aligned paper text with the calibrated runtime tier boundaries ($0.85$ and $0.50$). |
| **REV-10** | **Literature & Bib** | `references.bib` | Mangled citations: MINJA authors wrong, GhostWriter first names wrong, RouteLLM attributed to FrugalGPT, missing Louck (2026) and Singh (2026). | Novelty Reviewer | **PATCHED** `references.bib` with verified author lists, DOIs, arXiv identifiers, and added TMA-NM and Singh citations. |
