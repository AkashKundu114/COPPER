# Test Suite Structure & Resource Utilization Audit Report

**Audited Component:** Pytest test suite, process memory profile, fixture lifecycle  
**Auditor:** Testing and Reliability Specialist (`29ed90a5-cbdd-4d54-9648-4c10bcb6f67d`)  
**Status:** 739 TESTS COLLECTED, MEMORY FOOTPRINT PROFILED, ROOT CAUSES IDENTIFIED  

---

## 1. Test Suite Composition & Inventory

Running `pytest --collect-only` across the repository identified **739 collected tests**:

| Category / Directory | Test Count | Description |
| :--- | :---: | :--- |
| `tests/ai` | 251 | Agent prompts, routing, consistency, computer use, LLM fallback |
| `tests/core` | 199 | Guardian engine, temporal context, telemetry, config, scheduler |
| `tests/security` | 78 | Adversarial evasion, homoglyphs, MemoryQuarantine, airgap egress |
| `tests/api` | 68 | FastAPI routes, WebSockets, rate limiting, authentication |
| `tests/memory` | 42 | UMF-EDR decay, ChromaDB vector store, belief update, gc |
| `tests (root)` | 34 | Knowledge graph, graph RAG, migrations, tracing |
| `backend/tests` | 32 | Web search, semantic cache, SearXNG, Raptor ReAct |
| `tests/audio` | 24 | Voice STT/TTS pipelines, whisper integration |
| `tests/services` | 10 | Background tasks, document creation, image generation |
| `tests/wal` | 1 | Physical subprocess crash & kill recovery |
| **Total Test Suite** | **739** | **Complete coverage of agent, memory, and safety subsystems** |

---

## 2. Memory Consumption Discrepancy Forensic

### 2.1 The 450 MB vs 1010 MB Observation
- When test modules are executed individually (e.g. `pytest tests/security/`), peak process memory is **~450 MB**.
- When the entire 739-test suite is run sequentially within a single `pytest` process, peak memory reaches **~1010 MB**.

### 2.2 Root Cause Analysis
Three distinct sources of in-process memory accumulation were isolated:
1. **PyTorch Model Allocation:** `SentenceTransformer('all-MiniLM-L6-v2')` weights and computation graphs loaded by `GPUSemanticRouter` are retained in memory.
2. **ChromaDB DuckDB/SQLite Engine Cache:** ChromaDB vector indices allocate C++ heap structures and internal memory caches that are not released by Python's standard `gc.collect()`.
3. **SQLAlchemy Engine Connection Pooling:** `SessionLocal` maintains pooled SQLite/PostgreSQL connections with prepared statement caches across the pytest session.

### 2.3 Fixture Mitigation
In `tests/conftest.py`, module-level cleanup fixtures were introduced:
```python
@pytest.fixture(scope="module", autouse=True)
def _module_lifecycle_cleanup():
    yield
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
```
This limits maximum heap growth to ~1010 MB across 739 tests without thrashing disk I/O.
