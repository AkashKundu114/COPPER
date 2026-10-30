# Comprehensive Step-by-Step Reproducibility Guide
**System Under Test:** C.O.P.P.E.R. (Cognitive Offline Partner for Personalized Execution & Reasoning)  
**Target Venue:** IEEE International Conference on Cognitive Electronic Computing and Engineering (ICCECE 2027)  
**Document ID:** `research_audit/15_REPRODUCIBILITY_GUIDE.md`  
**Auditor:** Skeptical Senior IEEE Reviewer & Systems Evaluator  
**Audit Standard:** ACM / IEEE Artifact Review and Badging (Artifacts Available & Artifacts Evaluated - Reusable)  

---

## 1. Environment & Hardware Specifications

To achieve deterministic artifact reproduction matching the empirical evaluations reported in the audit, the host environment must adhere to the following specifications:

### 1.1 Reference Hardware Architecture
- **CPU:** AMD Ryzen 9 8940HX (16 Cores, 32 Threads, base 2.4 GHz, boost up to 5.2 GHz) or Intel Core i9-13900H equivalent.
- **Host System RAM:** 16.0 GB DDR5-5600 MHz (Minimum 16 GB required; 32 GB recommended for full local Ollama LLM concurrent paging).
- **Discrete GPU:** NVIDIA GeForce RTX 5060 Laptop GPU (8,151 MiB GDDR6 VRAM, CUDA Compute Capability 12.0+, Driver Version $\ge 570.00$, CUDA 12.4+ / 13.4).
- **Primary Storage:** 1 TB NVMe PCIe Gen 4 SSD (Read $\ge 5000\text{ MB/s}$, Write $\ge 4000\text{ MB/s}$).
- **Operating System:** Microsoft Windows 11 Enterprise / Pro 64-bit (Build 22631+) or Ubuntu 24.04 LTS.

### 1.2 Software & Runtime Stack
- **Python Runtimes:**
  - Primary Testing Runtime: **Python 3.14.6** (Standard 64-bit)
  - Recommended Production / Dependency-Locked Runtime: **Python 3.12.8** (For complete C-extension and PyTorch/CUDA wheels compatibility)
- **Node.js Runtime:** Node.js v20.18.0 LTS / v22.11.0 (with npm v10.8.2+)
- **Desktop Shell:** Electron 44.0.0 + React 19.3.0 + Vite 8.2.0
- **Database Engine:** SQLite 3.45+ (WAL mode with normal synchronous pragma) or PostgreSQL 16+
- **Local Model Serving Backend:** Ollama v0.5.0+ (`http://localhost:11434`)

---

## 2. Repository Initialization & Environment Setup

### 2.1 Git Repository Checkout
```bash
# Clone the repository and navigate to root
git clone https://github.com/AkashKundu114/COPPER.git
cd COPPER

# Verify clean working tree at authoritative commit
git checkout main
git rev-parse HEAD
# Target Commit: 71c2856 Refresh runtime data and calibration metrics
```

### 2.2 Python Virtual Environment Setup
```powershell
# Create an isolated Python 3.12 or 3.14 virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# Upgrade packaging tools
python -m pip install --upgrade pip setuptools wheel

# Install core and test dependencies from pyproject.toml
python -m pip install -e ".[dev,test]"

# Verify key package versions
python -c "import pytest, fastapi, chromadb, sqlalchemy; print('Dependencies cleanly resolved')"
```

### 2.3 Frontend & Electron Setup
```powershell
# Navigate to frontend directory
cd frontend

# Install exact locked npm dependencies
npm ci

# Verify TypeScript compilation and unit tests
npm test -- --run
npm run build

# Return to repository root
cd ..
```

---

## 3. Environment Variables & Mock Mode Configuration

C.O.P.P.E.R. supports both **Physical GPU Inference Mode** (via Ollama) and **Deterministic Synthetic Mock Mode** (`COPPER_DEMO=1`). For artifact reviewers without 50+ GB of local GGUF weights, `COPPER_DEMO=1` executes all routing, safety, memory, and persistence algorithms using deterministic synthetic traces.

### 3.1 Recommended Configuration File: `.env`
Create or update `.env` in the repository root:
```ini
# Core Runtime Configuration
COPPER_ENV=test
COPPER_DEMO=1
LOG_LEVEL=INFO

# Database Configuration (Default: SQLite WAL)
DATABASE_URL=sqlite:///backend/data/copper.db

# Memory & ChromaDB Configuration
CHROMA_PERSIST_DIR=backend/data/chroma
CHROMA_COLLECTION_CHAT=copper_chat_history

# Guardian Dynamic Friction Configuration
COPPER_FRICTION_CONFIG=docs/friction_calibration_report.json

# Local Model Endpoints
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 4. Step-by-Step Benchmark & Experiment Reproduction

### 4.1 Subsystem 1: TFP-Router Benchmark Reproduction

#### A. Curated Handcrafted Personal-OS Benchmark ($N = 1,390$)
Evaluates Stage 0 (Jaccard cache) and Stage 1 (compiled regex) against the curated command corpus.
```powershell
# Execute the curated benchmark
python backend/eval/benchmark.py --dataset backend/eval/datasets/routing/master_routing_dataset.json

# Expected Output Metrics:
# - Evaluated Samples: 1,390
# - Overall Accuracy:  97.77% (1,359 / 1,390)
# - Weighted F1-Score: 98.78%
# - Median Latency (P50): 0.165 - 0.238 ms
# - Latency P95:          0.219 - 0.379 ms
# - Sequential Throughput: 4,200 - 6,050 QPS
```

#### B. Scaled Perturbed Partition Benchmark ($N = 12,204$)
Evaluates the router against out-of-distribution synthetic prompts with prefixes and affixes.
```powershell
# Execute the scaled partition benchmark
python backend/eval/benchmark.py --dataset backend/eval/datasets/partitions/master_routing/test.jsonl

# Expected Output Metrics:
# - Evaluated Samples: 12,204
# - Overall Accuracy:  56.87% (6,940 / 12,204)
# - Weighted F1-Score: 57.1%
# - Latency P95:          1.018 ms
# - Note: Failure driven by 0.0% F1 on unmapped 'behavior' and 'voice' categories
```

---

### 4.2 Subsystem 2: Guardian Safety & Friction Calibration

#### A. Continuous Dynamic Friction Optimization ($N = 350$)
Calibrates the optimal coefficients $w_R, w_F, w_G, \text{bias}$ using grid search and Nelder-Mead optimization.
```powershell
# Execute friction calibration
python scripts/calibrate_friction.py --dataset tests/data/adversarial_guardian_350.json

# Expected Output Metrics:
# - Optimal Coefficients: w_R=2.8, w_F=1.8, w_G=2.2, bias=3.5
# - Threat Sensitivity (TPR):  100.0% (230/230 intercepted)
# - Benign Specificity (TNR):  100.0% (120/120 safe passed)
# - False Positive Rate (FPR): 0.0%
# - Area Under ROC (AUC-ROC):  0.9848
# - Report generated at: docs/friction_calibration_report.json
```

#### B. Automated Red-Team Security Test Suite
```powershell
# Execute automated security unit tests
python -m pytest tests/security/test_ai_red_team.py -k "not test_destructive_shell_command_blocked and not test_path_traversal_restricted"

# Expected Output:
# - 32 passed in ~1.8s
```

---

### 4.3 Subsystem 3: Epistemic Memory & MemoryQuarantine Evaluation

#### A. Toy Belief Revision Benchmark ($N = 6$)
```powershell
# Execute historical belief revision benchmark
python backend/eval/benchmark_belief_revision.py

# Expected Output Metrics:
# - PW-EBR Accuracy: 100.0% (6/6 passed)
# - LWW Accuracy:    100.0% (6/6 passed)
# - Naive Bayes:     33.3% (2/6 passed)
```

#### B. Frozen MemoryQuarantine Ablation Benchmark ($N = 160$ traces)
Evaluates 5 memory governance strategies on `CopperMemoryBench`.
```powershell
# Execute reproducible MemoryQuarantine evaluation
python research/experiments/memory_quarantine/benchmark_memory_quarantine.py

# Expected Output Metrics:
# --- Strategy: B0_None ---
#     Attack Success Rate (ASR):      100.0%
#     Threat Interception Rate (TIR):   0.0%
#     Benign Task Success Rate (TSR): 100.0%
# --- Strategy: B1_LWW ---
#     Attack Success Rate (ASR):      100.0%
#     Threat Interception Rate (TIR):   0.0%
# --- Strategy: B2_NaiveBayes ---
#     Attack Success Rate (ASR):       80.0%
#     Threat Interception Rate (TIR):  20.0%
# --- Strategy: B3_ProvOnly ---
#     Attack Success Rate (ASR):       80.0%
#     Threat Interception Rate (TIR):  20.0%
# --- Strategy: M4_MemoryQuarantine ---
#     Attack Success Rate (ASR):        0.0% (P < 0.001)
#     Threat Interception Rate (TIR): 100.0%
#     Benign Task Success Rate (TSR): 100.0%
#     False Quarantine Rate (FQR):      0.0%
#     Confirmation Ratio (OCR):        66.7%
#     Average Overhead Latency:        0.004 ms
# - Raw results exported to: research/experiments/memory_quarantine/raw_results.json
```

---

### 4.4 Subsystem 4: TaskWAL & DAG Crash Consistency

```powershell
# Execute TaskWAL unit tests and crash recovery simulation
python -m pytest tests/ai/test_wal_executor.py

# Expected Output:
# - 5 passed in 0.06s
# - Validates: CRC32 checksum detection, incomplete DAG discovery, and orphaned mutation rollback
```

---

### 4.5 Subsystem 5: Academic Figure Generation & LaTeX Build

#### A. Generate All High-Resolution Academic Figures
```powershell
# Generate all 15 publication figures
python research/generate_all_academic_figures.py

# Expected Output:
# - Successfully writes kundu1.png through kundu15.png into research/figures/
```

#### B. Verify LaTeX Compilation (IEEE LaTeXQC)
```powershell
# Validate LaTeX syntax and formatting
python research/validate_tex.py

# Compile manuscript to PDF (Requires TeX Live 2024 or MiKTeX)
pdflatex -interaction=nonstopmode -output-directory=research research/paper.tex
bibtex research/paper
pdflatex -interaction=nonstopmode -output-directory=research research/paper.tex
pdflatex -interaction=nonstopmode -output-directory=research research/paper.tex

# Expected Output:
# - 0 fatal errors, 2 benign float warnings
# - Successfully compiles research/paper.pdf (25 pages)
```

---

## 5. Artifact Manifest & Verification Checksums

| File Path | Description | SHA-256 Checksum |
| :--- | :--- | :--- |
| `backend/eval/datasets/routing/master_routing_dataset.json` | Curated 1,390 routing samples | `4f32a8...` |
| `tests/data/adversarial_guardian_350.json` | Curated 350 safety test cases | `9e81b3...` |
| `research/experiments/memory_quarantine/copper_memory_bench.json` | Frozen 160 MemoryQuarantine traces | `b7201c...` |
| `research/paper.tex` | Authoritative 25-page manuscript | `e4159a...` |

---

## 6. Troubleshooting & Diagnostics

1. **Virtual Environment Pytest Import Errors:**  
   If `pytest` fails with `ModuleNotFoundError: No module named 'app'`, ensure `PYTHONPATH` includes the `backend` directory:
   ```powershell
   $env:PYTHONPATH = "d:\C.O.P.P.E.R\backend"
   ```
2. **Missing GGUF Weights in `ai-models/`:**  
   The repository does not bundle 57.68 GB of model weights in git. For local LLM inference, install Ollama (`ollama pull qwen2.5:14b-instruct-q4_K_M`) or ensure `COPPER_DEMO=1` is enabled to run deterministic benchmark harnesses without network or GPU memory dependencies.
