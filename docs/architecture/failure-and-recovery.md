# Failure Modes, Resilience, and Autonomous Recovery

This document specifies how C.O.P.P.E.R. handles errors, resource exhaustion, crashes, timeouts, and cancellations across all architectural layers.

---

## 1. Principles of Resilient Operation

1. **Zero Silent Failures:** Every error produces an explainable, structured `ExecutionResult(status="error")` and is recorded in the cryptographic audit chain.
2. **Deterministic Rollback:** Side effects and partial filesystem/database mutations in multi-step DAG workflows are tracked by Write-Ahead Logging (`TaskWAL`) and rolled back on crash or cancellation.
3. **Graceful Degradation:** Hardware saturation (VRAM or queue full) sheds low-priority background work rather than crashing the system or freezing user interactions.
4. **Guaranteed Resource Cleanup:** Resource reservations (VRAM, locks, task descriptors) are de-allocated in guaranteed `finally` execution blocks.
5. **Asynchronous Fault Isolation:** Unhandled exceptions in background workers are routed to the `DeadLetterQueue` (`app.core.resilience.dead_letter_queue`) with backoff retries and forensic snapshots.

---

## 2. Failure Matrix & Remediation Strategies

| Failure Mode | Trigger / Condition | Detection Point | Automated Recovery Action |
|---|---|---|---|
| **VRAM Budget Saturation** | Model loading or concurrent inference approaches $\ge 85\%$ VRAM. | `ResourceAdmissionController`, `model_tier_manager` | Sheds background tasks; unloads idle LoRA adapters; invokes `dynamic_vram_compactor` to defragment KV-cache. |
| **Execution Timeout** | Operation exceeds `ResourceBudget.max_execution_time_seconds`. | `ArchitecturalControlPlane.execute_lifecycle` (`asyncio.wait_for`) | Cancels task, records timeout in audit log, executes state rollback, returns `status="error"`. |
| **User or Process Cancellation** | User clicks Stop or downstream dependency fails. | `CancellationToken.cancel()` | Halts pending steps in DAG, cancels active asyncio tasks, releases allocated resources. |
| **System Crash / Power Loss** | Hard OS termination or power failure during DAG execution. | Startup check in `lifespan` (`CrashRecoveryEngine`) | Scans `TaskWAL` log for uncommitted mutations and executes rollback for all incomplete DAGs. |
| **Tool Execution Exception** | Tool throws unhandled exception or script syntax error. | `ToolExecutor.execute()` | Catches exception, wraps in `ToolResult(success=False)`, logs to `DeadLetterQueue`, feeds observation back to LLM. |
| **Flaky Upstream Service** | External provider or local subprocess fails repeatedly. | `CircuitBreaker` (`Closed` -> `Open`) | Trips circuit breaker to open state; fails fast with cached response or degraded fallback; transitions to `Half-Open` on cooldown. |
| **Audit Chain Tampering** | Audit record hash does not match previous hash or signature. | `verify_audit_chain_integrity()` | Marks audit ledger as `UNAVAILABLE`, alerts operator sentinel, logs forensic intrusion warning. |

---

## 3. Crash Recovery Engine (`CrashRecoveryEngine`)

On startup in [`backend/app/main.py`](file:///d:/C.O.P.P.E.R/backend/app/main.py), the `lifespan` handler initializes `CrashRecoveryEngine`:

```python
from app.ai.orchestration.wal_executor import CrashRecoveryEngine

recovery_engine = CrashRecoveryEngine()
incomplete_dags = recovery_engine.find_incomplete_dags()
if incomplete_dags:
    logger.info(f"TaskWAL crash recovery: found {len(incomplete_dags)} incomplete DAGs. Performing rollback...")
    for dag_id in incomplete_dags:
        rolled_back = recovery_engine.rollback_uncommitted_mutations(dag_id)
        logger.info(f"TaskWAL rolled back {rolled_back} uncommitted mutations for DAG {dag_id}")
```

This guarantees atomicity and consistency even across abrupt desktop process terminations or workstation reboots.
