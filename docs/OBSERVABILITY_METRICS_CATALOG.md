# COPPER Observability Metrics Catalog

Comprehensive catalog of all native Prometheus metrics emitted by COPPER at `/metrics` and `/api/v1/telemetry/metrics`.

## 1. Hardware & Resource Metrics

| Metric Name | Type | Labels | Description | Alert Threshold |
| :--- | :--- | :--- | :--- | :--- |
| `copper_cpu_utilization_ratio` | Gauge | None | System CPU utilization ratio (0.0 to 1.0) | `> 0.92` (Warning) |
| `copper_ram_utilization_ratio` | Gauge | None | System RAM utilization ratio (0.0 to 1.0) | `> 0.90` (Critical) |
| `copper_ram_used_bytes` | Gauge | None | Total host RAM consumed in bytes | — |
| `copper_ram_total_bytes` | Gauge | None | Total host physical RAM available | — |
| `copper_gpu_utilization_ratio` | Gauge | None | GPU compute core utilization ratio (0.0 to 1.0) | — |
| `copper_vram_used_bytes` | Gauge | None | GPU VRAM memory consumed in bytes | `> 90% of total` (Critical) |
| `copper_vram_total_bytes` | Gauge | None | Total GPU VRAM budget (8GB hardware constraint) | — |

---

## 2. Model & Inference Telemetry

| Metric Name | Type | Labels | Description | Alert Threshold |
| :--- | :--- | :--- | :--- | :--- |
| `copper_model_loading_seconds` | Histogram | None | Time taken to load or hot-swap model into GPU VRAM (buckets: 0.5s to 30s) | `> 15s` (Warning) |
| `copper_llm_inference_duration_seconds` | Histogram | `model_name` | End-to-end inference request duration in seconds (buckets: 0.1s to 30s) | p95 `> 10s` |
| `copper_llm_tokens_generated_total` | Counter | `model_name` | Cumulative completion tokens generated | — |
| `copper_llm_prompt_tokens_total` | Counter | `model_name` | Cumulative prompt tokens evaluated | — |
| `copper_llm_tokens_per_second` | Gauge | `model_name` | Instantaneous token generation velocity (tokens/second) | `< 5.0` (Degraded) |
| `copper_inference_queue_depth` | Gauge | None | Count of queued inference requests waiting for execution | `> 5` (Warning), `> 10` (Critical) |

---

## 3. Agents & Tools Telemetry

| Metric Name | Type | Labels | Description | Alert Threshold |
| :--- | :--- | :--- | :--- | :--- |
| `copper_agent_executions_total` | Counter | `agent_type`, `status` | Total agent task executions partitioned by success or error | Error rate `> 20%` |
| `copper_agent_handoffs_total` | Counter | None | Total inter-agent task delegation handoffs | — |
| `copper_tool_executions_total` | Counter | `tool_name` | Cumulative count of tool invocations | — |
| `copper_tool_execution_duration_seconds` | Histogram | `tool_name` | Execution latency of tools (buckets: 10ms to 30s) | p95 `> 5s` |

---

## 4. HTTP & Traffiic Telemetry

| Metric Name | Type | Labels | Description | Alert Threshold |
| :--- | :--- | :--- | :--- | :--- |
| `copper_http_requests_total` | Counter | `method`, `path`, `status` | Total HTTP requests handled | HTTP 5xx rate `> 5%` |
| `copper_http_request_duration_seconds` | Histogram | `method`, `path` | HTTP request response latency in seconds | p95 `> 5s` |
| `copper_active_requests` | Gauge | None | Number of concurrent requests currently being processed | `> 50` |

---

## 5. Memory & Database Telemetry

| Metric Name | Type | Labels | Description | Alert Threshold |
| :--- | :--- | :--- | :--- | :--- |
| `copper_memory_retrieval_duration_seconds` | Histogram | None | ChromaDB / Vector store memory query duration in seconds | p95 `> 0.25s` |
| `copper_database_connection_status` | Gauge | None | Database connection probe health (1 = healthy, 0 = degraded) | `== 0` (Critical) |

---

## 6. Security & Guardian Telemetry

| Metric Name | Type | Labels | Description | Alert Threshold |
| :--- | :--- | :--- | :--- | :--- |
| `copper_security_events_total` | Counter | `event_type` | Security violations intercepted (e.g. rate limit, SSRF, injection) | `> 5/sec` (Spike) |
| `copper_guardian_verdicts_total` | Counter | `verdict` | Guardian safety verdicts (`allow`, `monitor`, `block`, `quarantine`) | Block surge |
| `copper_telemetry_pipeline_status` | Gauge | None | OpenTelemetry OTLP connection health (1 = healthy, 0 = degraded) | `== 0` (Warning) |
