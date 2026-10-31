# Routing, Orchestration & Model Fleet Audit Report

**Audited Modules:** `backend/app/ai/routing/router.py`, `backend/app/ai/orchestration/task_graph.py`, `backend/app/ai/llm/model_manager.py`  
**Git Commit Baseline:** `ed23f11`  
**Specialist Auditor:** Benchmark and Reproducibility Specialist (`0adf203e-1329-4ac3-9930-6f2e3e06fbf5`) & Runtime Auditor (`18458884-f127-4873-8175-78d81797cc85`)  
**Status:** FULLY BENCHMARKED, DATASETS VERIFIED, MODEL FLEET AUDITED  

---

## 1. Executive Summary

C.O.P.P.E.R employs a hierarchical routing topology:
1. **Tier 1 (Instant Deterministic Classifier):** Regex patterns, greetings, and direct intent triggers (latency: ~0.15 ms).
2. **Tier 2 (GPU Semantic Router):** Local embedding cosine similarity via `SentenceTransformer('all-MiniLM-L6-v2')` (latency: ~8.4 ms on CPU/GPU).
3. **Tier 3 (LLM Fallback Router):** Fast quantized model router when cosine confidence is borderline ($0.35 \le \text{sim} < 0.65$).

---

## 2. Benchmark Dataset Forensics (12,204 Query Evaluation)

### 2.1 The 76.69% vs 95.19% Accuracy Metric Discrepancy
An audit of the evaluation script `tests/ai/test_agent_router_benchmark.py` and benchmark dataset revealed a significant discrepancy:
- **Reported Accuracy in Literature/Manuscript:** ~95.2%
- **Raw Test Set Accuracy:** 76.69% (9,360 / 12,204 queries correct)

### 2.2 Root Cause Analysis
The 12,204 benchmark test set contains 2,372 queries labeled as `voice` and `behavior`.
However, C.O.P.P.E.R defines a **12-member `AgentType` enum**:
`chat`, `coding`, `automation`, `reminder`, `research`, `vision`, `planner`, `guardian`, `web_search`, `document`, `image`, `self_model`.

`voice` and `behavior` agents **do not exist** in C.O.P.P.E.R!
When `GPUSemanticRouter` evaluates these queries:
1. They map to no cluster centroid above threshold.
2. They are classified as Out-Of-Distribution (`unsupported_ood`).
3. They are safely routed to `chat` fallback.
4. The test harness scored this as an error because prediction (`chat`) $\ne$ label (`voice`).

**Corrected Metric:**
- On all **supported in-domain agent intents** (9,832 queries across the 12 active agents):
  $$\text{In-Domain Accuracy} = \frac{9,360}{9,832} = \mathbf{95.19\%}$$
- Across the entire raw dataset including intentionally rejected OOD queries:
  $$\text{Raw Accuracy} = \frac{9,360}{12,204} = \mathbf{76.69\%}$$

---

## 3. Model Fleet Audit

| Agent | Configured Model | VRAM / RAM Footprint | Inference Mode | Fallback Model |
| :--- | :--- | :---: | :---: | :--- |
| `chat` | `llama3.2:3b` | ~2.1 GB | Local Ollama | `qwen2.5:3b` |
| `coding` | `qwen2.5-coder:7b` | ~4.5 GB | Local Ollama | `llama3.2:3b` |
| `vision` (IRIS) | `qwen2.5-vl:3b` | ~3.2 GB | Local Ollama | `qwen2-vl:2b` |
| `automation` | `llama3.2:3b` | ~2.1 GB | Local Ollama | Rule engine |
| `router` | `all-MiniLM-L6-v2` | ~120 MB | PyTorch (Local) | Regex classifier |

**Fleet Memory Optimization:** Running tests serially maintains system memory within 450 MB. Running the complete 739-test suite in a single pytest process accumulates ~1010 MB due to PyTorch model weights and ChromaDB SQLite connection caching.
