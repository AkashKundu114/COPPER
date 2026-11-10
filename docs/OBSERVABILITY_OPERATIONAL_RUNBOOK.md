# COPPER Observability & Incident Response Operational Runbook

This runbook guides Site Reliability Engineers (SREs) and system operators in responding to COPPER performance alerts, resource exhaustion incidents, and telemetry degradations.

---

## 1. Alert Triage Playbooks

### A. Alert: `GPUVRAMPressure`
- **Severity**: Critical / Warning
- **Trigger**: GPU VRAM consumption `> 90%` of 8GB boundary or remaining headroom `< 500MB`.
- **Impact**: Risk of CUDA Out-Of-Memory (OOM) fatal crashes and forced process terminations during inference.
- **Diagnostic Steps**:
  1. Inspect active model allocation:
     ```bash
     curl -s http://localhost:8000/api/v1/telemetry/metrics | jq '.hardware'
     ```
  2. Query nvidia-smi / rocm-smi if accessible:
     ```powershell
     nvidia-smi --query-gpu=memory.used,memory.total --format=csv
     ```
  3. Verify which agent or image generator task is holding VRAM.
- **Remediation**:
  1. Trigger model hot-swap eviction: Send an unload instruction via `POST /api/v1/system/model/unload`.
  2. Switch reasoning agents from heavy tiers (e.g. 14B) to compact tiers (e.g. 7B/3B).
  3. If persistent, restart backend service to release leaked CUDA contexts.

---

### B. Alert: `InferenceQueueSaturation`
- **Severity**: Warning / Critical
- **Trigger**: `copper_inference_queue_depth > 5` for over 1 minute.
- **Impact**: Request timeouts, increased user latency, WebSocket disconnection drops.
- **Diagnostic Steps**:
  1. Check token generation velocity:
     ```bash
     curl -s http://localhost:8000/api/v1/telemetry/metrics | jq '.inference.tokens_per_second'
     ```
  2. Inspect trace log for stalling model requests:
     ```bash
     curl -s http://localhost:8000/api/v1/telemetry/traces?limit=10 | jq '.traces[] | {id: .trace_id, name: .root_name, duration: .duration_ms}'
     ```
- **Remediation**:
  1. Ensure Ollama daemon is running with hardware acceleration enabled.
  2. Enable request rate limiting at Traefik/FastAPI middleware to prevent thundering herd.

---

### C. Alert: `HighAgentFailureRate`
- **Severity**: Critical
- **Trigger**: `copper_agent_executions_total{status="error"}` exceeds 20% of total runs over a 5-minute window.
- **Impact**: Unsuccessful user tasks, infinite agent retry loops, degraded UX.
- **Diagnostic Steps**:
  1. Inspect error classification in structured JSON logs:
     ```powershell
     Select-String -Path data/logs/copper.jsonl -Pattern '"level": "ERROR"' | Select-Object -Last 20
     ```
  2. Check for missing tool permissions or sandbox execution rejections.
- **Remediation**:
  1. Verify Ollama model context length is sufficient for prompts.
  2. Inspect Guardian safety filters for false positive interventions.

---

### D. Alert: `DatabaseConnectivityDown`
- **Severity**: Critical
- **Trigger**: `copper_database_connection_status == 0`.
- **Impact**: Memory retrieval failure, inability to load session history or persist artifacts.
- **Diagnostic Steps**:
  1. Verify local SQLite database file accessibility and file lock status:
     ```powershell
     Test-Path data/copper.db
     ```
  2. Verify ChromaDB vector store health:
     ```bash
     curl -s http://localhost:8000/api/v1/memory/health
     ```
- **Remediation**:
  1. Check disk space: Ensure filesystem has at least 1GB free storage.
  2. Remove stale SQLite WAL lock files (`data/copper.db-wal`, `data/copper.db-shm`) if the host crashed.

---

### E. Alert: `SecurityIncidentSpike`
- **Severity**: Critical
- **Trigger**: `copper_security_events_total` increases by `> 5/sec` over 1 minute.
- **Impact**: Potential active prompt injection, credential exfiltration attempt, or brute force API attack.
- **Diagnostic Steps**:
  1. Inspect recent security events in audit trail:
     ```bash
     curl -s http://localhost:8000/api/v1/audit/ | jq '.events[0:10]'
     ```
  2. Filter `copper.jsonl` for security events:
     ```powershell
     Select-String -Path data/logs/copper.jsonl -Pattern '"security_event"' | Select-Object -Last 10
     ```
- **Remediation**:
  1. Temporarily revoke affected agent tokens or client session tokens.
  2. Review client IP and enable strict rate limiting.

---

## 2. Dashboard Directory & Provisioning

Grafana automatically provisions all six COPPER dashboards located in `infrastructure/grafana/provisioning/dashboards/definitions/`:

1. `copper_system_health.json`: System uptime, active connections, request throughput, and latency percentiles.
2. `copper_agent_performance.json`: Agent executions, success/failure ratios, inter-agent handoff rates, tool latencies.
3. `copper_model_inference.json`: Tokens per second, inference duration (p50/p95), queue depth, model loading times.
4. `copper_hardware_utilization.json`: GPU core utilization, 8GB VRAM allocation vs budget, host CPU and RAM.
5. `copper_security_events.json`: Intercepted security violations, Guardian verdict distributions (allow/block/quarantine).
6. `copper_memory_database.json`: ChromaDB vector retrieval latency, database query throughput.

---

## 3. Local Offline Operation

When external monitoring services (Prometheus, Loki, Tempo, Grafana) are disconnected or disabled:
- **Local Logs**: Stored continuously at `data/logs/copper.jsonl`.
- **In-Memory Metrics**: Available immediately via `GET /api/v1/telemetry/metrics`.
- **In-Memory Tracing**: The 200 most recent traces are accessible via `GET /api/v1/telemetry/traces` and `GET /api/v1/telemetry/traces/{trace_id}`.
- **In-Memory Alerting**: Active alerts are evaluated continuously and queryable via `GET /api/v1/telemetry/alerts`.
