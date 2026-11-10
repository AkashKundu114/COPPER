# COPPER Unified Observability Architecture Specification

## 1. Executive Summary & Design Principles

The COPPER Unified Observability Architecture provides end-to-end operational visibility across local AI agent execution, distributed model hot-swapping, sandboxed tool runs, vector memory retrievals, and zero-trust security events.

### Core Principles
1. **Local-First & Offline Resilience**: Observability never relies on cloud-only telemetry. In-memory metric buffers, bounded ring buffers, and local rotating JSON log files ensure COPPER functions 100% reliably when external monitoring services (Prometheus, Grafana, Loki, Tempo) are offline.
2. **8GB VRAM & Resource Headroom Tracking**: Continuous, low-overhead hardware sampling monitors the 8GB GPU VRAM boundary and host CPU/RAM to trigger proactive model unloads before out-of-memory (OOM) fatal events occur.
3. **End-to-End Correlation**: Every request, agent decision, tool execution, and log entry is correlated via OpenTelemetry `trace_id` and `span_id`.
4. **Data Privacy & Zero-Trust Redaction**: Sensitive user credentials, bearer tokens, API keys, and raw private prompts are masked before hitting log sinks or Prometheus label dimensions.

---

## 2. Telemetry Pillars

```
                     ┌───────────────────────────────────────────────┐
                     │          User Request / Client Turn          │
                     └───────────────────────┬───────────────────────┘
                                             │ [Trace Context: trace_id, span_id]
                                             ▼
                     ┌───────────────────────────────────────────────┐
                     │            Context Construction               │
                     └───────────────────────┬───────────────────────┘
                                             ▼
                     ┌───────────────────────────────────────────────┐
                     │          Memory & Vector Retrieval            │
                     └───────────────────────┬───────────────────────┘
                                             ▼
                     ┌───────────────────────────────────────────────┐
                     │           Reasoning & Model Router            │
                     └───────────────────────┬───────────────────────┘
                                             ▼
                     ┌───────────────────────────────────────────────┐
                     │         Agent Execution (e.g. Vulcan)         │
                     └───────────────────────┬───────────────────────┘
                                             ▼
                     ┌───────────────────────────────────────────────┐
                     │         Sandboxed Tool Execution              │
                     └───────────────────────┬───────────────────────┘
                                             ▼
                     ┌───────────────────────────────────────────────┐
                     │      Response Assembly & Guardian Scan        │
                     └───────────────────────────────────────────────┘
                                             │
                  ┌──────────────────────────┼──────────────────────────┐
                  ▼                          ▼                          ▼
          [Structured Logs]          [Prometheus Metrics]       [Distributed Traces]
          (copper.jsonl / Loki)      (/metrics / Prometheus)     (LiveSpanCollector/Tempo)
```

### A. Structured JSON Logs (`app.core.json_logger`)
- **Format**: High-throughput JSON line (`.jsonl`) emitted to both standard error/console and rotating file sink at `data/logs/copper.jsonl` (15MB max file size, 5 backup generations).
- **Core Schema**:
  - `timestamp`: ISO8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SS.mmmmmm+00:00`).
  - `service`: Service identity (`copper`).
  - `level`: Log severity level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
  - `logger`: Name of the emitting module.
  - `message`: Sanitized log text.
  - `trace_id`: 32-character hexadecimal OpenTelemetry trace correlation ID.
  - `span_id`: 16-character hexadecimal span ID.
  - `session_id`: Client session or turn identifier.
  - `agent_id` / `agent_type`: Identifier and archetype of active agent.
  - `task_id`: Scheduled or active task identifier.
  - `model_name`: AI model involved in the operation.
  - `tool_name`: Invoked tool name.
  - `security_event`: Security classification if an intervention occurred.
  - `duration_ms`: Duration of execution stage in milliseconds.
- **Redaction Filter**: `RedactingFilter` executes regex masking across bearer tokens, API keys (`sk-...`, `Bearer ...`), and password parameters prior to disk persistence.

### B. Prometheus Metrics Registry (`app.core.metrics`)
- **Zero-Dependency Core**: In-memory registry implementing `Counter`, `Gauge`, and `Histogram` with support for labeled dimensions, percentile bucketing, and Prometheus exposition rendering (`text/plain; version=0.0.4`).
- **Hardware Telemetry**: Emits CPU utilization, RAM usage, GPU compute utilization, and VRAM consumption against the 8GB hardware budget.
- **Inference & Routing**: Tracks token generation velocity (tokens/second), model load/hot-swap latencies, prompt/completion token counters, and queue backlogs.
- **Exposition Endpoints**:
  - `GET /metrics`: Standard Prometheus scrape endpoint consumed by Prometheus server.
  - `GET /api/v1/telemetry/metrics`: Rich JSON summary consumable by frontend dashboards and diagnostic clients.

### C. Distributed Tracing (`app.core.telemetry`)
- **Span Hierarchy**: Propagates trace context across synchronous and asynchronous operations using `TraceContextTextMapPropagator`.
- **LiveSpanCollector**: In-memory ring buffer holding the most recent 200 distributed traces with sub-millisecond start offsets, statuses, and full attribute maps.
- **Tempo Integration**: Dual export to Grafana Tempo via gRPC OTLP exporter (`http://tempo:4317`) when available, with automatic graceful fallback to local ring-buffer queries when offline.

---

## 3. AI-Specific Observability Dimensions

| Telemetry Dimension | Metric / Attribute | Purpose |
| :--- | :--- | :--- |
| **Model Selection** | `router.selected_agent`, `router.confidence` | Audits routing accuracy and cognitive scoring confidence |
| **Hot-Swapping Duration** | `copper_model_loading_seconds` | Tracks model tier transitions and VRAM load latency |
| **Inference Latency** | `copper_llm_inference_duration_seconds` | Measures TTFT (Time to First Token) and total completion time |
| **Token Velocity** | `copper_llm_tokens_per_second` | Tracks tokens/second generation speed across quantization levels |
| **Queue Depth** | `copper_inference_queue_depth` | Detects pipeline saturation before requests time out |
| **Memory Latency** | `copper_memory_retrieval_duration_seconds` | Isolates ChromaDB / vector retrieval search overhead |
| **Guardian Verdicts** | `copper_guardian_verdicts_total{verdict}` | Monitors safety blocks, quarantines, and approvals |

---

## 4. Alert Sentinel & In-App Anomaly Detection (`app.core.alert_sentinel`)

The architecture incorporates `AlertSentinel`, a dual-mode alerting engine:
1. **Prometheus Alertmanager Rules** (`infrastructure/prometheus/alerts.yml`): For enterprise or clustered deployments.
2. **Local In-App Sentinel Engine**: Evaluates thresholds directly in-process and serves alerts via `GET /api/v1/telemetry/alerts` without requiring external Alertmanager daemons.

### Firing Rules
- `GPUVRAMPressure`: Fired when VRAM exceeds 90% allocation or less than 500MB headroom remains.
- `HostCPUExhaustion`: Sustained CPU utilization above 92%.
- `HostRAMExhaustion`: System memory pressure above 90%.
- `InferenceQueueSaturation`: Pending inference backlog exceeds 5 requests.
- `HighAgentFailureRate`: Greater than 20% agent task execution failures over recent window.
- `ModelLoadFailures`: Detected model loading or hot-swapping errors.
- `DatabaseConnectivityDown`: Database probe failure.
- `SecurityIncidentSpike`: Abnormal surge in security violations or prompt injection attempts.
- `TelemetryPipelineDegraded`: OTLP export failures or span buffer drops.
