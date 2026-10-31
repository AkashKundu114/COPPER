# C.O.P.P.E.R. Empirical Reproducibility Guide
**Document ID:** `REPRODUCIBILITY_GUIDE.md`  
**Target Repository:** `d:\C.O.P.P.E.R`  
**Date:** October 31, 2026  
**Auditor:** Senior Verification Engineer & Systems Architect  
**Hardware Environment:** AMD Ryzen 9 8940HX | NVIDIA GeForce RTX 5060 Laptop GPU | Windows 11 Enterprise | Python 3.14.6 (`backend/.venv`)

---

## 1. Quick-Start Verification Commands

To independently reproduce all audited claims and benchmarks, run the following commands from the repository root:

### 1.1 Run Full Automated Test Suite (730+ Tests)
```powershell
& "backend\.venv\Scripts\python.exe" -m pytest tests/ -v
```
Expected outcome: All test suites pass cleanly. Total RSS memory stays below 750 MB.

### 1.2 Reproduce MemoryQuarantine Benchmark (160 Traces)
```powershell
& "backend\.venv\Scripts\python.exe" research/experiments/memory_quarantine/benchmark_memory_quarantine.py
```
Expected output:
- B0_None: ASR = 100.0%, TIR = 0.0%
- B1_LWW: ASR = 100.0%, TIR = 0.0%
- B2_NaiveBayes: ASR = 80.0%, TIR = 20.0%
- B3_ProvOnly: ASR = 80.0%, TIR = 20.0%
- M4_MemoryQuarantine: **ASR = 0.0%, TIR = 100.0%, TSR = 100.0%, FQR = 0.0%, OCR = 70.0%**
- Average latency overhead: ~0.004 ms

### 1.3 Reproduce Physical Subprocess Crash Recovery Test
```powershell
& "backend\.venv\Scripts\python.exe" scripts/test_real_subprocess_crash.py
```
Expected output:
1. Spawns physical child worker subprocess with distinct OS PID.
2. Applies uncommitted disk writes (`secret_key.txt` created, `config.json` overwritten).
3. Injects brutal `taskkill /F /PID <pid>` process crash.
4. `CrashRecoveryEngine` detects `crashed_dag_001` with 2 uncommitted mutations.
5. Idempotent compensations unlinks `secret_key.txt` and restores `config.json` to pre-image.
6. Returns exit code 0 (`PHYSICAL POST-CRASH INTEGRITY VERIFIED`).

### 1.4 Reproduce Routing & Guardian Scaled Benchmarks (23,705 Samples)
```powershell
& "backend\.venv\Scripts\python.exe" backend/eval/benchmark.py
```
Expected output:
- Routing Accuracy: **76.69%** (12,204 samples, P95: 3.27 ms, throughput: ~453 QPS)
- Guardian Accuracy: **99.45%** (11,501 samples, 63 breaches, latency: 0.048 ms)
- Generates `backend/eval/benchmark_report.md` and `backend/eval/benchmark_metrics.json`.

---

## 2. Environment & Dependency Alignment

- Python: `3.14.6` in `backend/.venv` (CUDA 13.4 PyTorch for GPU semantic router).
- Node.js: `v24.19.0` for frontend React 19 / Electron 44 desktop runtime.
- Pytest plugins: `pytest-asyncio`, `pytest-cov`, `pytest-mock`.
- Virtual Display: `DISPLAY=:99` (configured automatically via `conftest.py` for headless environments).
