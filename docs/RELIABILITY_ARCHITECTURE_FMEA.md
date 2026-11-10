# COPPER Reliability Architecture & Failure-Modes and Effects Analysis (FMEA)

## 1. Executive Summary & Design Principles

The COPPER Reliability & Resilience Architecture provides fault tolerance across AI agent execution, tiered model hot-swapping under an 8GB VRAM constraint, persistent workflow resumption, and database lock contention.

### Core Architecture Principles
1. **Local-First Crash Consistency**: Uses an ARIES-inspired Write-Ahead Log (WAL) with CRC32 checksums and idempotency keys to ensure zero committed task loss during process termination or kernel crashes.
2. **Cascading Failure Prevention**: Subsystems (Ollama LLM, Vector Store, Sandboxed Tools, External APIs) are shielded by concurrency-safe Circuit Breakers and exponential backoff with full decorrelated jitter.
3. **Graceful Model Degradation**: Heavy 14B model crashes, out-of-memory states, or inference timeouts degrade to the pinned gatekeeper model (`qwen2.5:1.5b`) rather than aborting client requests.
4. **Idempotent Workflow Resumption**: Interrupted multi-agent DAGs resume from the last valid checkpoint without repeating external side effects or corrupting files.
5. **Dead-Letter Queue Isolation**: Unrecoverable, poisoned tasks are isolated to `data/dlq/dlq_records.jsonl` to prevent infinite execution loops.

---

## 2. Measurable Reliability Objectives (SLOs)

| Metric | Target | Definition / Measurement |
| :--- | :--- | :--- |
| **Availability (Local Services)** | **99.9%** | Uptime of FastAPI backend, SQLite WAL, and local memory services. |
| **Recovery Time Objective (RTO) - Models** | **< 5.0 seconds** | Time required to detect a model timeout/crash and fail over to gatekeeper. |
| **Recovery Time Objective (RTO) - Workflows**| **< 2.0 seconds** | Time to inspect WAL, compensate uncommitted files, and resume DAG. |
| **Recovery Point Objective (RPO)** | **0 Committed Tasks** | Zero committed sub-task outputs lost upon process crash. In-flight uncommitted task step is cleanly rolled back and re-executed. |
| **Task Completion Reliability** | **> 99.5%** | Percentage of user DAG workflows reaching terminal completion (via primary or fallbacks). |
| **Circuit Breaker Trip Latency** | **< 1 millisecond** | Fast-fail response time when downstream service circuit is OPEN. |

---

## 3. Subsystem Fault Isolation Architecture

```
                       ┌────────────────────────────────────────┐
                       │          Client Turn / Request         │
                       └───────────────────┬────────────────────┘
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │         InferenceQueueManager          │
                       │  (Priorities, Concurrency, Timeouts)   │
                       └───────────────────┬────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐              ┌──────────────────┐
│   Ollama LLM     │             │ Multi-Agent DAG  │              │  SQLite / Vector │
│  Circuit Breaker │             │   TaskGraphWAL   │              │   Resilient DB   │
│  (14B -> 1.5B)   │             │ (ARIES Resumption)              │ (Retry Transient)│
└──────────────────┘             └──────────────────┘              └──────────────────┘
         │                                 │                                 │
         └─────────────────────────────────┼─────────────────────────────────┘
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │           Dead-Letter Queue            │
                       │     (data/dlq/dlq_records.jsonl)       │
                       └────────────────────────────────────────┘
```

---

## 4. Failure Modes and Effects Analysis (FMEA)

| Failure Mode | Root Cause | Severity | Detection Mechanism | Automated Recovery Mechanism | Residual Risk |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Model Process Crash (Ollama SIGKILL / 500)** | CUDA OOM, driver crash, or daemon death | **High** | `httpx.RequestError`, `ConnectionResetError` | `CircuitBreaker` trips; `ModelTierManager` falls back immediately to pinned gatekeeper model (`qwen2.5:1.5b`). | Gatekeeper model provides lower reasoning depth for complex coding tasks. |
| **Inference Timeout / Hang** | Massive context length or model infinite generation loop | **Medium** | `InferenceQueueManager` deadline watchdog (`asyncio.wait_for`) | Cancels task future after `timeout_s` (default 60s); invokes fallback coroutine without stalling queue. | Prompt tokens consumed up to the timeout. |
| **SQLite Database Lock Contention** | Concurrent writers under burst requests | **Medium** | `sqlite3.OperationalError: database is locked` | `execute_resilient_transaction` executes exponential backoff with full jitter (up to 3 retries); WAL pragma minimizes locks. | Burst latencies increase by 100ms - 500ms during lock contention. |
| **Interrupted DAG Execution** | Sudden power outage, host shutdown, or SIGKILL | **High** | `CrashRecoveryEngine.find_incomplete_dags()` at startup | Rolls back uncommitted file mutations; `prepare_dag_resumption()` loads committed task outputs and resumes remaining nodes without repeating side effects. | None; side effects are strictly idempotency-guaranteed. |
| **Corrupted WAL Record** | Partial sector write during unexpected disk power cut | **Medium** | CRC32 checksum mismatch in `WALRecord.calculate_checksum()` | `salvage_corrupted_wal()` quarantines corrupt line into `quarantine_dag_{id}.bad`, re-writing valid records. | The single damaged in-flight record must be recomputed. |
| **Poison Pill Task Input** | Malformed prompt causing deterministic agent crashes | **Low** | Bounded retries exhausted in `SelfHealingEngine` | Automatically enqueued to `DeadLetterQueue` (`dlq_records.jsonl`); prevents retry loops from starving worker slots. | Manual operator inspection required to replay via DLQ API. |
| **Redis Cache Unavailability** | Redis daemon stopped or socket timed out | **Low** | `aioredis` connection error caught at init | `redis_client` defaults to `None`; system falls back transparently to local process memory cache. | Cache is non-shared across separate OS processes. |
| **ChromaDB Vector Outage** | Vector store port unreachable or collection lock | **Medium** | `resilient_call` catching `ChromaError` | Degrades to in-memory episodic context or keyword memory retriever. | Semantic vector ranking unavailable during outage. |
