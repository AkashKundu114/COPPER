# Critical Research Issue Register & Vulnerability Ledger
**Target Venue:** IEEE International Conference on Cognitive Electronic Computing and Engineering (ICCECE 2027)  
**System Under Test:** C.O.P.P.E.R. (Cognitive Offline Partner for Personalized Execution & Reasoning)  
**Document ID:** `research_audit/17_CRITICAL_ISSUE_REGISTER.md`  
**Auditor:** Skeptical Senior IEEE Reviewer & Systems Evaluator  
**Audit Standard:** Strict Archival Verification & Peer Review Defensibility  

---

## 1. Evidence Verification Taxonomy

Every finding in this register is categorized under one of six strict, non-negotiable verification states:
- **`VERIFIED`:** Confirmed by direct execution, source code inspection, and reproducible empirical telemetry.
- **`PARTIALLY VERIFIED`:** Mechanism exists in code or holds on small sub-corpora, but falls short of broader quantitative claims.
- **`UNVERIFIED`:** Claim asserted in manuscript without empirical measurement or reproducible script.
- **`CONTRADICTED`:** Direct empirical measurement or source code actively disproves the published manuscript claim.
- **`INVALID`:** Conceptual or methodological premise is fundamentally flawed or scientifically unsupportable.
- **`PROPOSED`:** Recommended architectural modification or remediation protocol awaiting implementation.

---

## 2. Exhaustive Critical Issue Register

### ISS-01: Routing Accuracy Collapse Under Out-of-Distribution Perturbations
- **Severity:** **`CRITICAL`**
- **Category:** Integrity & Empirical Validation
- **Status:** **`CONTRADICTED`**
- **Manuscript Location:** `paper.tex`: Abstract (line 66), §III.A, Table I (line 1002)
- **Source Files:** `backend/app/ai/orchestration/agent_router.py:600-750`, `backend/eval/benchmark_report.md:11`
- **Finding:**  
  The manuscript claims the CPU cascade router achieves **97.77% Top-1 accuracy** and **98.78% weighted F1** across 1,390 empirical samples. While independently replicated on the handcrafted `master_routing_dataset.json` (1,390 queries matching regex keyword patterns), evaluating the identical router against the repository's scaled 12,204-sample perturbed dataset (`backend/eval/datasets/partitions/master_routing/test.jsonl`) results in a catastrophic collapse to **56.87% accuracy** (Weighted F1: 57.1%).
- **Technical Root Cause:**  
  1. `agent_router.py` relies heavily on rigid regex patterns (`COMPILED_KEYWORD_RULES`). Synthetic conversational modifiers, affixes, and noise words cause regex misses, dumping queries into conversational fallback (`chat`).
  2. The scaled benchmark introduced `behavior` and `voice` intent categories which do not exist in `AgentType` (`constants.py:7-45`), resulting in **0.0% Precision and 0.0% Recall** for both classes (accounting for 2,372 test cases).
- **Required Action:**  
  1. Candidly report both the 97.77% curated accuracy and the 56.87% out-of-distribution stress-test result in the revised manuscript.
  2. Implement Stage 1.5 semantic embedding classification (`nomic-embed-text`) and Stage 2 SLM fallback as specified in `13_ABLATION_AND_EXPERIMENT_PLAN.md` to restore OOD accuracy to $\ge 88\%$.
- **Experiment Required:** Yes (Subsystem 1 Routing Ablation C1–C6).

---

### ISS-02: Concealed Safety Breaches on Scaled Benchmark Evaluation
- **Severity:** **`CRITICAL`**
- **Category:** Safety & Integrity
- **Status:** **`CONTRADICTED`**
- **Manuscript Location:** `paper.tex`: Abstract (line 66), §III.C, Fig. 7 (line 665)
- **Source Files:** `backend/app/core/guardian.py:109-178`, `backend/eval/benchmark_report.md:57-59`
- **Finding:**  
  The manuscript asserts: *"Across 1,740 functional and adversarial test cases, the safety layer achieves 99.83% threat-catch sensitivity (1,737/1,740 intercepted; 100.0% on red-team triggers) with zero false-positive friction on benign workflows."*  
  In reality:
  1. The 1,740 corpus does not exist as an independent, frozen test dataset. The curated dataset (`tests/data/adversarial_guardian_350.json`) contains exactly 350 samples (230 threats, 120 benign), on which TPR is 100%.
  2. When evaluated against the repository's scaled 11,501-sample threat partition (`backend/eval/datasets/partitions/threats/test.jsonl`), Guardian achieved **93.3% sensitivity**, permitting **770 dangerous security breaches (6.7% False Negative Rate)** to bypass safety boundaries undetected.
- **Technical Root Cause:**  
  Adversarial perturbations involving semantic rephrasing, compound instructions, and unseen obfuscated payloads bypass the static regex patterns in `SAFETY_PATTERNS`.
- **Required Action:**  
  1. Retract the unverified 1,740 sample / 99.83% claim from the manuscript.
  2. Transparently publish both the 100.0% sensitivity on $N=350$ curated cases and the 93.3% sensitivity on $N=11,501$ scaled stress cases.
  3. Deploy semantic zero-shot classifier fallback for ambiguous tool calls.
- **Experiment Required:** Yes (Subsystem 3 Safety Ablation S0–S5).

---

### ISS-03: Mischaracterization of User-Space Runtime as an "Operating System"
- **Severity:** **`CRITICAL`**
- **Category:** Architecture & Conceptual Overclaiming
- **Status:** **`INVALID`**
- **Manuscript Location:** Title, Abstract (line 66), §I (lines 74–106), §II (lines 126–175)
- **Source Files:** `backend/app/main.py`, `frontend/electron-main.cjs`, `research/notes/gap_analysis.md:5-10`
- **Finding:**  
  The paper markets C.O.P.P.E.R. as a "Sovereign Personal AI Operating System." In computer engineering, an operating system manages hardware abstraction, kernel/user-space CPU protection rings (Ring 0 vs Ring 3), virtual memory paging tables, preemptive hardware interrupt dispatch, and filesystem drivers. C.O.P.P.E.R. is an application-level user-space Python/FastAPI web service communicating with SQLite and Ollama via HTTP, packaged inside an Electron desktop GUI.
- **Technical Root Cause:**  
  Marketing terminology used interchangeably with technical systems architecture.
- **Required Action:**  
  Retitle and re-frame the manuscript from an indefensible "Operating System" to an unassailable systems paper: *"MemoryQuarantine: Consequence-Aware Persistent Memory Integrity and Dynamic Friction for Edge Multi-Agent Runtimes"* or *"A Resource-Bounded Edge Multi-Agent Runtime"*.
- **Experiment Required:** No (Manuscript scope and structural restructuring).

---

### ISS-04: Hardcoded Inference Throughput Arrays in Figure Generation Script
- **Severity:** **`HIGH`**
- **Category:** Empirical Reproducibility & Scientific Telemetry
- **Status:** **`CONTRADICTED`**
- **Manuscript Location:** `paper.tex`: §IV.E, Fig. 1 (line 102), Fig. 3 (line 251)
- **Source Files:** `research/generate_all_academic_figures.py:116, 146`
- **Finding:**  
  Figure 1 and Figure 3 depict generation throughput acceleration (e.g., 38.08 tok/s for 14B models, 133 tok/s for 3B, 216 tok/s for 1.5B). Inspection of `generate_all_academic_figures.py` reveals that these values are hardcoded literal Python lists (`after_tps = [38.08, 37.76, 36.87, 39.02, 47.72]`) rather than dynamic data loaded from reproducible model execution logs.
- **Technical Root Cause:**  
  Figure scripts were written as synthetic mock generators during early prototyping and never connected to real benchmark output JSONs.
- **Required Action:**  
  Replace all hardcoded Python arrays in `generate_all_academic_figures.py` with dynamic parsers reading timestamped CSV/JSON execution logs from actual Ollama model benchmarks on consumer hardware.
- **Experiment Required:** Yes (Empirical local model throughput profiling).

---

### ISS-05: Declared 57.68 GB Model Fleet Absent from Physical Storage
- **Severity:** **`HIGH`**
- **Category:** Systems & Artifact Verification
- **Status:** **`PARTIALLY VERIFIED`**
- **Manuscript Location:** `paper.tex`: §III.E, §IV.D, Table III (line 873)
- **Source Files:** `ai-models/models_manifest.json:68`, `scripts/verify_audit_numbers.py:27-29`
- **Finding:**  
  Table III and `models_manifest.json` specify a 15-model fleet totaling 57.68 GB (38.45 GiB on disk). A scan of the local physical storage (`ai-models/`) reveals that only 6.17 GiB of physical weights exist (`sd_turbo.safetensors` at 4.86 GiB and audio/TTS models at 1.31 GiB). The directories `ai-models/core/`, `ai-models/subagents/`, and `ai-models/vision/` contain only empty `.gitkeep` files.
- **Technical Root Cause:**  
  Large GGUF files are excluded from git tracking to comply with GitHub file size boundaries. The system relies on an external Ollama daemon (`http://localhost:11434`) or runs in synthetic mock mode (`COPPER_DEMO=1`).
- **Required Action:**  
  Clarify in Table III and §IV.D that Table III specifies architectural manifest capacity, and explicitly document that GGUF weights are served dynamically via the external Ollama cache.
- **Experiment Required:** No.

---

### ISS-06: Agent Fleet Inflation (30 Claimed Roles vs 12 Core Enum Agents)
- **Severity:** **`HIGH`**
- **Category:** System Architecture & Claim Consistency
- **Status:** **`CONTRADICTED`**
- **Manuscript Location:** `paper.tex`: Abstract (line 66), §I, §III, §IV.D
- **Source Files:** `backend/app/core/constants.py:7-45`, `REMEDIATION/CLAIMS_AUDIT.md:13`
- **Finding:**  
  The manuscript asserts that C.O.P.P.E.R. coordinates a "30-agent functional fleet." Inspection of `backend/app/core/constants.py` shows that the `AgentType` enum contains strictly **12 core specialized agents** (`chat`, `coding`, `document`, `automation`, `reminder`, `research`, `vision`, `image`, `web_search`, `campaign_intelligence`, `planner`, `guardian`).
- **Technical Root Cause:**  
  The "30" count combines the 12 core agents with 18 sub-agent task personas and catalog templates defined in `backend/data/agency_agents_full_catalog.json`.
- **Required Action:**  
  Correct all text across `paper.tex` and `README.md` to specify: **12 core functional agents** orchestrated with **18 specialized sub-agent task personas**.
- **Experiment Required:** No.

---

### ISS-07: Epistemic Belief Revision Validated on an Underpowered Toy Dataset
- **Severity:** **`HIGH`**
- **Category:** Methodology & Statistical Validity
- **Status:** **`PARTIALLY VERIFIED`**
- **Manuscript Location:** `paper.tex`: §III.B, §IV.C, Fig. 6
- **Source Files:** `backend/eval/benchmark_belief_revision.py:21-65`
- **Finding:**  
  Section §IV.C claims that Provenance-Weighted Epistemic Belief Revision (PW-EBR) achieves superior accuracy over Last-Write-Wins (LWW) and Naive Bayes. Running `benchmark_belief_revision.py` reveals that the entire benchmark consists of only **6 hand-authored synthetic scenarios**. Testing on $N=6$ lacks statistical validity and provides zero evidence of resilience against delayed memory poisoning.
- **Technical Root Cause:**  
  Early proof-of-concept testing was never updated with an external or large-scale memory poisoning dataset.
- **Required Action:**  
  Replace the $N=6$ toy evaluation with the reproducible 160-trace `CopperMemoryBench` evaluation (`research/experiments/memory_quarantine/benchmark_memory_quarantine.py`) demonstrating statistically significant defense against delayed memory poisoning ($p < 0.001$).
- **Experiment Required:** Yes (MemoryQuarantine evaluation).

---

### ISS-08: Overstatement of Regex Filter as a "Zero-Trust Data Firewall & Airgap"
- **Severity:** **`MEDIUM`**
- **Category:** Security & Threat Model Scope
- **Status:** **`PARTIALLY VERIFIED`**
- **Manuscript Location:** `paper.tex`: Abstract (line 117), §III.D, Fig. 8
- **Source Files:** `backend/app/core/data_firewall.py:1-120`
- **Finding:**  
  The manuscript claims a "Zero-Trust Data Firewall" that "eliminates outbound token exfiltration at the subprocess boundary." Inspection of `data_firewall.py` reveals that it is an in-memory string regex sanitizer matching 17 compiled patterns (credit cards, SSNs, API tokens). It does not hook Windows network sockets, does not interface with the Windows Filtering Platform (WFP), and does not inspect raw TCP/UDP streams.
- **Technical Root Cause:**  
  Exaggerated systems terminology applied to application-level string masking.
- **Required Action:**  
  Downgrade manuscript prose to accurately characterize the module as an **in-memory regular-expression redaction and privacy sanitizer**.
- **Experiment Required:** No.

---

### ISS-09: Multi-Agent DAG Crash Recovery Validated on Small Trial ($N = 5$)
- **Severity:** **`MEDIUM`**
- **Category:** Reliability & Experimental Power
- **Status:** **`PARTIALLY VERIFIED`**
- **Manuscript Location:** `paper.tex`: §III.F, Fig. 12
- **Source Files:** `tests/ai/test_wal_executor.py`, `paper.tex:119`
- **Finding:**  
  The paper claims DAG crash consistency validated with 5/5 recoveries. While the implementation of `TaskWAL` and `CrashRecoveryEngine` in `wal_executor.py` is structurally sound, a sample size of $N=5$ yields a 95% Clopper-Pearson confidence interval of [47.8%, 100.0%], which is too wide for an IEEE archival venue.
- **Technical Root Cause:**  
  Unit tests verified functionality, but a multi-cycle stress benchmark was not automated.
- **Required Action:**  
  Execute $N=500$ automated crash simulations injecting failures at diverse execution points to establish a 95% lower bound $\ge 99.4\%$.
- **Experiment Required:** Yes (Persistence Ablation P2).

---

### ISS-10: Test Suite Process Memory Leak (RSS Exceeds 750 MB Threshold)
- **Severity:** **`MEDIUM`**
- **Category:** Systems & Memory Footprint
- **Status:** **`VERIFIED`**
- **Manuscript Location:** `paper.tex`: §IV.D
- **Source Files:** `tests/core/test_resource_benchmarks.py:15-22`
- **Finding:**  
  Running the complete pytest test suite causes `test_process_memory_footprint` to fail with 1,010.97 MB RSS, breaching the 750 MB ceiling. In isolation, the test passes at ~450 MB RSS. Accumulated imports and open ChromaDB vector store clients across 687 tests cause memory bloat.
- **Technical Root Cause:**  
  Absence of explicit test-suite teardown fixtures to release ChromaDB and PyTorch memory allocations between test modules.
- **Required Action:**  
  Implement teardown fixtures in `conftest.py` calling `gc.collect()` and closing ChromaDB connection handles.
- **Experiment Required:** No.

---

### ISS-11: Outdated Framework References in Legacy Documentation
- **Severity:** **`LOW`**
- **Category:** Documentation Hygiene
- **Status:** **`VERIFIED`**
- **Manuscript Location:** Historical documentation notes
- **Source Files:** `frontend/package.json:20-25`, `REMEDIATION/CLAIMS_AUDIT.md:15-16`
- **Finding:**  
  Several repository documents reference Tauri v2 desktop runtime and React 18. The current production codebase uses Electron 44 and React 19.3.0.
- **Required Action:**  
  Purge all remaining references to Tauri and React 18 across docs.
- **Experiment Required:** No.

---

### ISS-12: Sidebar View Count Mismatch (13 vs 16 Navigation Views)
- **Severity:** **`INFORMATIONAL`**
- **Category:** UI Documentation Consistency
- **Status:** **`VERIFIED`**
- **Manuscript Location:** System overview documentation
- **Source Files:** `frontend/src/components/layout/Sidebar.tsx:27-43`
- **Finding:**  
  Documentation states a 13-section sidebar, whereas `Sidebar.tsx` renders 16 navigation views.
- **Required Action:**  
  Update documentation to reflect 16 navigation views.
- **Experiment Required:** No.
