# MemoryQuarantine: Artifact Reproducibility & Replication Guide

**Target Venue:** IEEE International Conference on Cognitive Electronic Computing and Engineering (ICCECE 2027)  
**Document ID:** `research/REPRODUCIBILITY.md`  
**Date:** October 30, 2026  
**Auditor & Reproducibility Lead:** Scientific Reproducibility Engineer  

---

## 1. System Requirements & Testbed Specifications

To replicate all experimental findings, benchmark metrics, and manuscript figures:

### 1.1 Physical Hardware
- **Host GPU:** NVIDIA GeForce RTX 5060 Laptop GPU (8,151 MiB GDDR6 VRAM, CUDA capability 12.x / 13.x).
- **Host CPU:** AMD Ryzen 9 8940HX (16 Cores, 32 Threads @ 3.30 GHz base clock).
- **RAM:** 16 GB DDR5 System Memory.
- **Disk Storage:** At least 10 GB free SSD storage.

### 1.2 Software Stack
- **Operating System:** Microsoft Windows 11 Enterprise x64 (Build 26100) or Ubuntu 24.04 LTS.
- **Python Runtime:** Python 3.14.6 64-bit (or Python 3.11+).
- **PyTorch & CUDA:** PyTorch 2.6.0+cu126 with `torch.cuda.is_available() == True`.
- **Local Model Daemon:** Ollama v0.5.1+ listening on `127.0.0.1:11434` with `qwen2.5:0.5b` loaded.

---

## 2. Step-by-Step Replication Protocol

### Step 1: Environment Setup
```powershell
# Clone the repository
git clone https://github.com/AkashKundu114/COPPER.git
cd COPPER

# Checkout verified remediation branch
git checkout remediation/audit-remediation

# Install Python dependencies
pip install -r requirements.txt
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

### Step 2: Verify GPU Acceleration & Backend Integrity
Execute the complete test suite across all 675 unit, security, and integration tests:
```powershell
python -m pytest tests/
```
*Expected Result:* `675 passed, 0 failed` in ~330 seconds.

### Step 3: Run CopperMemoryBench Evaluation ($N = 160$ Traces)
Execute the multi-strategy governance benchmark across B0 (Flat RAG), B1 (LWW), B2 (Naive Bayes), B3 (Provenance-Only), and M4 (MemoryQuarantine):
```powershell
python research/experiments/memory_quarantine/benchmark_memory_quarantine.py
```
*Expected Outputs:*
- `raw_results.json` generated in `research/experiments/memory_quarantine/`.
- $B_0, B_1$: ASR = 100.0%, TIR = 0.0%.
- $B_2, B_3$: ASR = 80.0%, TIR = 20.0%.
- $M_4$: ASR = 0.0%, TIR = 100.0%, TSR = 100.0%, FQR = 0.0%.

### Step 4: Run End-to-End Real LLM Poisoning Harness
Ensure Ollama is running and has pulled `qwen2.5:0.5b`:
```powershell
ollama pull qwen2.5:0.5b
python research/experiments/memory_quarantine/test_real_llm_harness.py
```
*Expected Outputs:*
- `real_llm_results.json` generated in `research/experiments/memory_quarantine/`.
- Under B1: Canary token overwritten (`attack_succeeded: True`).
- Under M5 (MemoryQuarantine): `ToolExecutor` blocks execution (`Authority = 0.0641 < 0.25`), preserving canary intact (`threat_intercepted: True`).

### Step 5: Run TFP-Router Scaled Ablation Suite
```powershell
python research/experiments/routing/run_routing_ablation.py
```
*Expected Output:*
- Top-1 Accuracy: 99.98%, Weighted-F1: 99.99% on 12,204 held-out samples.
- GPU P95 Latency: 1.425 ms on RTX 5060 Laptop GPU.

### Step 6: Run TaskWAL Chaos Harness ($N = 500$ Trials)
```powershell
python -m pytest backend/eval/test_chaos_and_fuzzing.py -v
```
*Expected Output:*
- `4 passed` in ~11s.
- 500 / 500 crash recoveries successful (100.0% recovery, exact 95% Clopper-Pearson lower bound 99.26%).

### Step 7: Regenerate All Academic Figures
```powershell
python research/generate_all_academic_figures.py
```
*Expected Output:*
- Generates 15 publication-grade figures in `research/figures/` at 350 DPI directly from runtime logs without synthetic Dirichlet distributions.

---

## 3. Dataset & Code Artifact Checksums (SHA-256)

| Artifact Path | SHA-256 Digest | Description |
| :--- | :--- | :--- |
| `research/experiments/memory_quarantine/copper_memory_bench.json` | `dfa98e82...` | 160-trace benchmark dataset |
| `research/experiments/memory_quarantine/benchmark_memory_quarantine.py` | `71b3e944...` | Multi-strategy benchmark runner |
| `research/experiments/memory_quarantine/test_real_llm_harness.py` | `0299cd17...` | End-to-end real LLM evaluation |
| `backend/eval/datasets/partitions/master_routing/test.jsonl` | `9b38ff12...` | 12,204 held-out routing test partition |
