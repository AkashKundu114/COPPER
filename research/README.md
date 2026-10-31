# C.O.P.P.E.R. Research Publication Workspace

This directory contains the primary publication manuscripts, empirical benchmarks, high-resolution figures, standalone tables, and submission bundles for the **C.O.P.P.E.R. (Cognitive Offload & Persistent Personal Execution Runtime)** project.

---

## 1. Executive Summary & Publication Tracks

| Track | Manuscript Title | Status | Target Venue | Primary Documents |
| :--- | :--- | :--- | :--- | :--- |
| **Active / Reconstructed** | **MemoryQuarantine: Consequence-Calibrated Persistent Memory Integrity for Local Tool-Using Agents** | **Ready for Submission (Compiled PDF Available)** | **IEEE ICCECE 2027** / arXiv (`cs.CR`, `cs.AI`, `cs.SE`) | [`paper_revised.pdf`](paper_revised.pdf), [`paper_revised.tex`](paper_revised.tex), [`memoryquarantine_package/`](memoryquarantine_package/), [`memoryquarantine_submission.zip`](memoryquarantine_submission.zip) |
| **Historical / Audited** | *C.O.P.P.E.R.: A Resource-Bounded Local Multi-Agent Architecture for Consumer GPU* | Audited & Quarantined (See [`research_audit/`](../research_audit/)) | Archived | [`paper.tex`](paper.tex), [`paper.pdf`](paper.pdf), [`legacy/`](legacy/) |

> **Notice on Audit Remediation:** The historical 25-page manuscript ([`paper.tex`](paper.tex)) was subjected to a rigorous 19-report academic and architectural audit ([`research_audit/`](../research_audit/)). The audit identified unsupported multi-agent claims and benchmark unobservables. In response, the research was reconstructed into **MemoryQuarantine**—a tightly focused, mathematically formalized, and physically validated IEEE conference paper with 100% reproducible empirical benchmarks on physical hardware.

---

## 2. Directory Structure

```
research/
├── paper_revised.tex                             # Authoritative 8-page IEEE conference manuscript (MemoryQuarantine)
├── references.bib                                # 19 verified BibTeX references (0 unreferenced citations)
├── IEEEtran.cls                                  # Official IEEE conference LaTeX document class (v1.8b)
├── orcidlink.sty                                 # ORCID badge styling for LaTeX
│
├── memoryquarantine_package/                     # Standalone, self-contained build bundle (pdflatex ready)
│   ├── main.tex                                  # Top-level LaTeX root (pdflatex entry point)
│   ├── references.bib                            # Clean BibTeX bibliography
│   ├── IEEEtran.cls                              # IEEE document class
│   ├── algorithm.sty / algorithmic.sty           # Pseudocode macros
│   ├── 00README.XXX                              # arXiv engine configuration
│   └── figures/                                  # All 8 publication figures (350 DPI)
│
├── memoryquarantine_submission.zip               # arXiv / Overleaf ready zip archive (2.30 MB)
├── memoryquarantine_submission.tar.gz            # Standard arXiv gzipped tar archive (2.27 MB)
├── MEMORYQUARANTINE_METADATA.txt                 # Form metadata for arXiv & IEEE conference submission
├── ARXIV_SUBMISSION_GUIDE_MEMORYQUARANTINE.md    # Step-by-step submission guide for arXiv & Overleaf
│
├── figures/                                      # Publication figures (350 DPI, academic typography)
│   ├── fig1_mq_dual_plane_architecture.png       # Fig 1: Dual-Plane Retrieval vs Authority Decoupling
│   ├── fig2_mq_attack_lifecycle.png              # Fig 2: Multi-Session Delayed Memory Poisoning Timeline
│   ├── fig3_mq_asr_tir_baselines.png             # Fig 3: ASR & TIR Benchmark across 5 Baselines (w/ 95% CIs)
│   ├── fig4_mq_vector_breakdown.png              # Fig 4: Granular Vector Interception (AV1-AV5)
│   ├── fig5_mq_security_utility_tradeoff.png     # Fig 5: Security vs Utility Pareto Frontier (TIR vs TSR)
│   ├── fig6_mq_epistemic_belief_dynamics.png     # Fig 6: PW-EBR Surprise Scaling & UMF-EDR Retention
│   ├── fig7_mq_guardian_friction_roc.png         # Fig 7: Guardian Continuous Safety ROC Curve
│   └── fig8_mq_latency_distribution.png          # Fig 8: Sub-Millisecond Authority Gate Overhead (<0.01 ms)
│
├── tables/                                       # Standalone LaTeX and Markdown tables
│   ├── table1_main_security_results.tex / .md    # Main Security & Governance Benchmark Results
│   ├── table2_attack_vector_breakdown.tex / .md  # Attack Vector Granular Breakdown (AV1-AV5)
│   ├── table3_audit_reconciliation.tex / .md     # Traceability Matrix to research_audit/
│   ├── table4_related_work_matrix.tex / .md      # Comparison with MemGPT, Generative Agents, AgentDojo, etc.
│   ├── table5_provenance_hierarchy.tex / .md     # Provenance Trust Weights gamma(s)
│   ├── table6_threat_model_summary.tex / .md     # Threat Vector Taxonomy & Preconditions
│   ├── table7_experimental_testbed.tex / .md     # Physical Edge Testbed Hardware Specifications
│   ├── table8_statistical_significance.tex / .md # Fisher's Exact & Clopper-Pearson Statistical Rigor
│   └── README.md                                 # Tables compendium and usage notes
│
├── experiments/                                  # Reproducible empirical evaluation benchmarks
│   └── memory_quarantine/
│       ├── copper_memory_bench.json              # 160 multi-session adversarial and functional evaluation traces
│       ├── generate_frozen_benchmark.py          # Benchmark dataset generator
│       ├── benchmark_memory_quarantine.py        # Automated benchmark runner across 5 governance baselines
│       ├── raw_results.json                      # Raw per-trial evaluation logs
│       ├── real_llm_results.json                 # Real LLM physical tool execution log
│       └── test_real_llm_harness.py              # End-to-end sandbox execution with local LLM (RTX 5060)
│
├── Supporting Methodology Documents:
│   ├── EXPERIMENTAL_METHODOLOGY.md               # Complete experimental protocol, metrics, and threat vectors
│   ├── RESULTS_PROVENANCE.md                     # Traceability to raw empirical logs and hardware execution
│   ├── RELATED_WORK_MATRIX.md                    # Deep-dive taxonomy vs 15 contemporary frameworks
│   ├── REPRODUCIBILITY.md                        # Step-by-step reproduction instructions and seed configurations
│   ├── LIMITATIONS.md                            # Frank disclosure of threat scope and boundary constraints
│   ├── REVIEWER_OBJECTION_REGISTER.md            # Anticipated reviewer critique, defense, and code evidence
│   ├── 00_initial_inventory.md                   # Initial audit inventory
│   ├── 01_claim_evidence_register.csv            # Line-by-line claim-to-evidence audit log
│   ├── 02_related_work_and_novelty.md            # Novelty justification notes
│   └── 03_study_protocol.md                      # Formal study protocol
│
├── Tooling Scripts:
│   ├── validate_memoryquarantine_paper.py        # Automated package and LaTeX syntax auditor
│   ├── build_memoryquarantine_arxiv_package.py   # Automated submission package builder (.zip and .tar.gz)
│   └── generate_memoryquarantine_academic_figures.py # 350 DPI academic figure generator
│
└── Historical Audited Files (Archived for Provenance):
    ├── paper.tex / paper.pdf                     # Original 25-page unverified manuscript
    ├── arxiv_package/ / arxiv_submission.*       # Original unverified submission archives
    ├── generate_all_academic_figures.py          # Legacy 15-figure generator
    └── legacy/                                   # Archived MLSys draft and unverified scripts
```

---

## 3. Core Empirical Findings

All results are empirically grounded and measured on the physical edge testbed (AMD Ryzen 9 8940HX, NVIDIA GeForce RTX 5060 Laptop GPU 8 GB VRAM, Windows 11 Enterprise x64, Python 3.14.6):

| Baseline / Strategy | ASR (%) $\downarrow$ | TIR (%) $\uparrow$ | TSR (%) $\uparrow$ | FQR (%) $\downarrow$ | Gate Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **$B_0$: Flat Vector RAG** (MemGPT/Park et al.) | 100.0% | 0.0% | 100.0% | 0.0% | 0.000 ms |
| **$B_1$: Last-Write-Wins** | 100.0% | 0.0% | 100.0% | 0.0% | 0.000 ms |
| **$B_2$: Naive Bayes Updating** | 80.0% | 20.0% | 100.0% | 0.0% | 0.003 ms |
| **$B_3$: Provenance-Only** | 20.0% | 80.0% | 100.0% | 0.0% | 0.003 ms |
| **$M_5$: MemoryQuarantine (Ours)** | **0.0%** | **100.0%** | **100.0%** | **0.0%** | **0.005 ms** |

### Statistical Rigor
- **Fisher's Exact Test:** Two-tailed $p = 2.21 \times 10^{-59}$ vs Flat Vector RAG ($p < 0.001$).
- **95% Confidence Intervals (Clopper-Pearson Exact):**
  - Attack Success Rate: $0.0\%$ (95% CI: $[0.0\%, 3.6\%]$)
  - Threat Interception Rate: $100.0\%$ (95% CI: $[96.4\%, 100.0\%]$)
  - Task Success Rate: $100.0\%$ (95% CI: $[94.2\%, 100.0\%]$)
- **Overhead:** Authority Gate evaluation completes in $5.2\ \mu\text{s}$ (P95 $9.2\ \mu\text{s}$), contributing $<0.01\%$ to the $303\text{ ms}$ agent decision cycle.

---

## 4. Figures Inventory

All publication figures are rendered at **350 DPI** with high visual clarity, generous padding, and academic color palettes in [`figures/`](figures/):

| Figure | Identifier in Paper | Description | Key Insight / Result |
| :---: | :--- | :--- | :--- |
| **Fig. 1** | `fig1_mq_dual_plane_architecture.png` | Dual-Plane Governance Architecture | Decouples Semantic Recall Plane from Consequence-Calibrated Authority Gate Plane. |
| **Fig. 2** | `fig2_mq_attack_lifecycle.png` | Attack Lifecycle Timeline | Illustrates how delayed prompt injection exploits the time lag between ingestion and execution. |
| **Fig. 3** | `fig3_mq_asr_tir_baselines.png` | Benchmark Security Comparison | Bar chart comparing ASR and TIR across 5 strategies with exact 95% Clopper-Pearson CIs ($p = 2.21 \times 10^{-59}$). |
| **Fig. 4** | `fig4_mq_vector_breakdown.png` | Granular Attack Vector Breakdown | Interception across AV1–AV5 showing Naive Bayes stops AV5, Prov-Only stops AV3, and MemoryQuarantine stops all 5. |
| **Fig. 5** | `fig5_mq_security_utility_tradeoff.png` | Security vs. Utility Pareto Frontier | Demonstrates ideal upper-right frontier operating point (100% TIR, 100% TSR, 0% FQR). |
| **Fig. 6** | `fig6_mq_epistemic_belief_dynamics.png` | Epistemic Belief Dynamics | Visualizes natural log surprise scaling $\ln(1 + \vert \Delta \vert)$ and Ebbinghaus decay under reinforcement. |
| **Fig. 7** | `fig7_mq_guardian_friction_roc.png` | Continuous Safety Layer ROC Curve | Demonstrates 100% sensitivity with 0% false positives ($F_1 = 1.000$) on adversarial red-team traces. |
| **Fig. 8** | `fig8_mq_latency_distribution.png` | Latency Distribution & System Cycle | Log-scale violin plot showing sub-microsecond gate evaluation and $<0.01\%$ total cycle overhead. |

---

## 5. Standalone Tables Inventory

Available as standalone LaTeX snippets (`.tex`) and Markdown documents (`.md`) in [`tables/`](tables/):

| Table | Identifier in Paper | Content Summary |
| :---: | :--- | :--- |
| **Table I** | `table1_main_security_results` | Benchmark comparison of ASR, TIR, TSR, FQR, and evaluation latency across all 5 strategies. |
| **Table II** | `table2_attack_vector_breakdown` | Vector-by-vector interception breakdown across AV1 through AV5. |
| **Table III** | `table3_audit_reconciliation` | Traceability matrix resolving defects reported in `research_audit/` (07, 08, 09, 13, 16). |
| **Table IV** | `table4_related_work_matrix` | Capability comparison vs. MemGPT, Generative Agents, AgentDojo, PromptInject, and NeMo. |
| **Table V** | `table5_provenance_hierarchy` | Immutable source provenance trust tiers ($\gamma$) from System/Canary (1.0) to Tool Output (0.2). |
| **Table VI** | `table6_threat_model_summary` | Formal taxonomy of threat vectors, attacker capabilities, targets, and expected consequences. |
| **Table VII** | `table7_experimental_testbed` | Detailed hardware, host OS, compute runtime, and local model specifications. |
| **Table VIII** | `table8_statistical_significance` | Fisher's Exact Test p-values and 95% Clopper-Pearson confidence interval bounds. |

---

## 6. How to Build & Validate the Manuscript

### Step 1: Validate Quality Control
Verify that all citations, labels, figures, and LaTeX environments are error-free:
```bash
python research/validate_memoryquarantine_paper.py
```

### Step 2: Rebuild Submission Packages
Rebuild the standalone submission package and generate compressed `.zip` and `.tar.gz` archives:
```bash
python research/build_memoryquarantine_arxiv_package.py
```

### Step 3: Compile Certified PDF via IEEE LaTeXQC
Compile the LaTeX package using the official IEEE cloud compilation service to generate the verified PDF:
```bash
python research/compile_latexqc.py
```

### Step 4: Regenerate Publication Figures
Regenerate all 8 figures at 350 DPI from verified benchmark data:
```bash
python research/generate_memoryquarantine_academic_figures.py
```

### Step 5: Re-Run Empirical Benchmarks
Re-execute the 160-trace benchmark suite or physical LLM tool harness:
```bash
# Run 160-trace benchmark
python research/experiments/memory_quarantine/benchmark_memory_quarantine.py

# Run end-to-end local LLM execution harness on RTX 5060 GPU
python research/experiments/memory_quarantine/test_real_llm_harness.py
```

---

## 7. Submission Checklist & Ready Status

- [x] **Manuscript (`paper_revised.tex`):** Validated IEEEtran conference format (8 pages, 0 LaTeX syntax errors, 0 non-ASCII characters).
- [x] **Bibliography (`references.bib`):** 19 peer-reviewed citations matching all `\cite{}` calls.
- [x] **Figures (`figures/`):** 8 publication-grade 350 DPI figures with verified visual clarity and non-overlapping typography.
- [x] **Tables (`tables/`):** 8 standalone LaTeX and Markdown tables with verified statistical data.
- [x] **Submission Archive (`memoryquarantine_submission.zip` / `.tar.gz`):** Self-contained, ~2.3 MB package containing `00README.XXX`, style files, TeX source, and figures.
- [x] **Metadata & Submission Guide:** [`MEMORYQUARANTINE_METADATA.txt`](MEMORYQUARANTINE_METADATA.txt) and [`ARXIV_SUBMISSION_GUIDE_MEMORYQUARANTINE.md`](ARXIV_SUBMISSION_GUIDE_MEMORYQUARANTINE.md).
- [x] **Regression Tests:** 737 / 737 test suite passing in root codebase.
