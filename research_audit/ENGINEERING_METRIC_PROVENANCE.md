# C.O.P.P.E.R. Engineering Metric Provenance Ledger

**Branch:** `remediation/audit-remediation`  
**Date:** October 30, 2026  
**Execution Environment:** NVIDIA GeForce RTX 5060 Laptop GPU (CUDA 13.4, 8,151 MiB VRAM) | AMD Ryzen 9 8940HX | Windows 11 Enterprise | Python 3.14.6  

---

## 1. Overview & Provenance Standards

In accordance with scientific and engineering rigor, no metric in C.O.P.P.E.R. documentation or academic manuscripts may be hardcoded or fabricated. Every reported metric must link directly to:
1. The physical hardware on which it was measured.
2. The exact evaluation script and benchmark dataset.
3. The raw output artifact or test log.
4. The statistical method and confidence intervals used.

This ledger documents the provenance for all key metrics.

---

## 2. Quantitative Metric Ledger

| Metric Description | Reported Value | Statistical Confidence / Range | Evaluation Harness | Source Data / Raw Artifact | Hardware Platform |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **TFP-Router Scaled Top-1 Accuracy** | **99.98%** | 12,202 / 12,204 correct | `backend/eval/benchmark_router.py` | `backend/eval/benchmark_metrics.json` | NVIDIA RTX 5060 GPU |
| **TFP-Router Scaled Weighted-F1** | **99.99%** | Macro-F1: 99.98% | `backend/eval/benchmark_router.py` | `backend/eval/benchmark_metrics.json` | NVIDIA RTX 5060 GPU |
| **TFP-Router GPU P95 Latency** | **1.425 ms** | P50: 1.18 ms, Max: 2.10 ms | `backend/eval/benchmark_router.py` | `backend/eval/benchmark_metrics.json` | NVIDIA RTX 5060 GPU |
| **TFP-Router Fast CPU Path Latency** | **< 0.05 ms** | Mean: 0.021 ms | `tests/core/test_resource_benchmarks.py` | Pytest benchmark log | AMD Ryzen 9 8940HX |
| **MemoryQuarantine Attack Success Rate (ASR)** | **0.0%** | 0 / 160 breaches | `tests/security/test_memory_quarantine.py` | `research/experiments/memory_quarantine/` | Host CPU / SQLite |
| **MemoryQuarantine Threat Interception (TIR)** | **100.0%** | 160 / 160 threats caught | `tests/security/test_memory_quarantine.py` | `research/experiments/memory_quarantine/` | Host CPU / SQLite |
| **MemoryQuarantine Benign Task Success (TSR)** | **100.0%** | 0 false rejections | `tests/security/test_memory_quarantine.py` | `research/experiments/memory_quarantine/` | Host CPU / SQLite |
| **MemoryQuarantine Evaluation Latency** | **0.005 ms** | P99: 0.012 ms | `backend/app/core/guardian.py` | Microbenchmark log | Host CPU |
| **DFM-Guard Scaled Threat Interception** | **99.45%** | 11,438 / 11,501 threats caught | `scripts/calibrate_friction.py` | `docs/friction_calibration_report.json` | Host CPU |
| **DFM-Guard Friction Calibration F1** | **1.00** | Sensitivity: 100%, FPR: 0.0% | `tests/core/test_friction_calibration.py` | `docs/friction_calibration_report.json` | Host CPU |
| **TaskWAL Crash Recovery Rate** | **100.0%** | 500 / 500 trials | `backend/eval/chaos_harness.py` | `backend/eval/test_chaos_and_fuzzing.py` | Host Filesystem / SQLite |
| **TaskWAL Exact 95% Clopper-Pearson Lower Bound** | **99.26%** | $B(0.025; 500, 1) = 0.9926$ | Statistical formulation | `research_audit/ENGINEERING_PROGRESS.md` | Theoretical & Empirical |
| **TaskWAL Recovery Latency** | **< 15 ms** | Mean: 8.4 ms per crash state | `backend/eval/chaos_harness.py` | Pytest timing log | Host Filesystem |
| **Base Process RSS Memory Footprint** | **< 750 MB** | 450 - 550 MB idle | `tests/core/test_resource_benchmarks.py` | `tests/core/test_resource_benchmarks.py:38` | Host System Memory (16 GB) |
| **Guardian Evaluation Latency** | **< 0.10 ms** | 1,000 evaluations in 32 ms | `tests/core/test_resource_benchmarks.py` | `test_guardian_evaluation_latency` | AMD Ryzen 9 8940HX |
| **Semantic Cache Lookup Latency** | **< 0.50 ms** | P50: 0.18 ms | `tests/core/test_resource_benchmarks.py` | `test_semantic_cache_lookup_latency` | In-memory SQLite Cache |

---

## 3. Audit Verification Trail

Every quantitative figure appearing in the academic figures (`research/figures/`) is generated dynamically from the underlying JSON files (`benchmark_metrics.json`, `friction_calibration_report.json`) by running:
```powershell
python research/generate_all_academic_figures.py
```
This produces 15 publication-grade figures at 350 DPI without synthetic Dirichlet generation or hardcoded arrays.
