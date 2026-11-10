# COPPER Reliability & Disaster Recovery Operational Runbook

This runbook guides Site Reliability Engineers (SREs), system administrators, and operators in diagnosing, mitigating, and recovering from component crashes, circuit trips, dead-letter accumulation, and workflow interruptions.

---

## 1. Circuit Breaker Inspection and Manual Recovery

COPPER manages named circuit breakers (`ollama_llm`, `tool_web_search`, `chroma_retrieval`, etc.) to prevent cascading failures.

### A. Inspect Circuit Breaker Status
Query circuit breaker telemetry via Python or CLI:
```powershell
.\backend\.venv\Scripts\python.exe -c "
from app.core.resilience.circuit_breaker import circuit_breaker_registry
for stats in circuit_breaker_registry.list_all():
    print(f'Breaker: {stats.name} | State: {stats.state} | Failures: {stats.failure_count} | Tripped: {stats.total_tripped_count}')
"
```

### B. Manually Reset Tripped Circuit Breakers
If a downstream dependency (e.g. Ollama daemon) has been restored and you want to bypass the cool-down timer immediately:
```powershell
.\backend\.venv\Scripts\python.exe -c "
import asyncio
from app.core.resilience.circuit_breaker import circuit_breaker_registry
asyncio.run(circuit_breaker_registry.reset_all())
print('All circuit breakers reset to CLOSED state.')
"
```

---

## 2. Dead-Letter Queue (DLQ) Management

Unrecoverable tasks and poison pills are stored at `data/dlq/dlq_records.jsonl`.

### A. List Active Dead-Letter Records
```powershell
.\backend\.venv\Scripts\python.exe -c "
from app.core.resilience.dead_letter_queue import dead_letter_queue
records = dead_letter_queue.list_records(include_replayed=False)
print(f'Active unhandled dead letters: {len(records)}')
for r in records[-5:]:
    print(f'Task ID: {r.task_id} | Service: {r.origin_service} | Reason: {r.failure_reason}')
"
```

### B. Mark Record as Replayed / Purge
```powershell
.\backend\.venv\Scripts\python.exe -c "
from app.core.resilience.dead_letter_queue import dead_letter_queue
purged = dead_letter_queue.purge_replayed()
print(f'Purged {purged} replayed records.')
"
```

---

## 3. Write-Ahead Log (WAL) Inspection & Workflow Resumption

COPPER persists all multi-agent DAG task executions into append-only WAL files at `data/wal/dag_{dag_id}.wal`.

### A. Detect Interrupted Workflows
```powershell
.\backend\.venv\Scripts\python.exe -c "
from app.ai.orchestration.wal_executor import crash_recovery_engine
incomplete = crash_recovery_engine.find_incomplete_dags()
print(f'Incomplete DAG runs detected: {incomplete}')
for dag_id in incomplete:
    print(crash_recovery_engine.analyze_dag_state(dag_id))
"
```

### B. Resume an Interrupted Workflow Safely
```powershell
.\backend\.venv\Scripts\python.exe -c "
from app.ai.orchestration.wal_executor import crash_recovery_engine
dag_id = 'YOUR_INCOMPLETE_DAG_ID'
if crash_recovery_engine.can_resume_dag(dag_id):
    prep = crash_recovery_engine.prepare_dag_resumption(dag_id)
    print(f'Resumption prepared. Restored {len(prep[\"committed_tasks\"])} committed tasks. In-flight mutations compensated: {prep[\"compensated_mutations_count\"]}')
"
```

### C. Salvage Corrupted WAL Files
If a sector corruption occurred during power loss:
```powershell
.\backend\.venv\Scripts\python.exe -c "
from app.ai.orchestration.wal_executor import crash_recovery_engine
dag_id = 'YOUR_CORRUPTED_DAG_ID'
res = crash_recovery_engine.salvage_corrupted_wal(dag_id)
print(f'Salvage result: {res}')
"
```

---

## 4. Database Disaster Recovery & Backups

SQLite WAL database files reside at `data/copper.db`.

### A. Run Database Integrity Check & Verified Snapshot
```powershell
.\backend\.venv\Scripts\python.exe -c "
from app.database.postgres import verify_and_backup_db
result = verify_and_backup_db()
print('Backup & Integrity Result:', result)
"
```

### B. Truncate / Checkpoint SQLite WAL
If `data/copper.db-wal` grows excessively during heavy transactional batches:
```powershell
.\backend\.venv\Scripts\python.exe -c "
from app.database.postgres import checkpoint_wal
result = checkpoint_wal('TRUNCATE')
print('WAL Checkpoint Result:', result)
"
```

---

## 5. Model Failure & VRAM Pressure Mitigation

1. **Verify Ollama daemon status**:
   ```powershell
   Get-Process -Name "ollama" -ErrorAction SilentlyContinue
   ```
2. **If Ollama crashed**:
   Restart the Ollama daemon:
   ```powershell
   ollama serve
   ```
   COPPER's circuit breaker will transition to `HALF_OPEN` and auto-close upon the next canary request.
3. **If GPU VRAM is over-allocated**:
   Issue an immediate model unload to release CUDA context:
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:11434/api/chat" -Method POST -Body '{"model": "qwen2.5-coder:14b", "keep_alive": 0}' -ContentType "application/json"
   ```
   COPPER automatically maintains the pinned gatekeeper (`qwen2.5:1.5b`) for continuous operations.
