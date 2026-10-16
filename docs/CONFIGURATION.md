# C.O.P.P.E.R. Configuration Reference

**Comprehensive Guide to Environment Variables, Configuration Tiers, and Platform Defaults**

C.O.P.P.E.R. manages configuration via Pydantic `BaseSettings` defined in [`backend/app/core/config.py`](file:///D:/C.O.P.P.E.R/backend/app/core/config.py). Variables can be declared in a `.env` file at the project root or passed as system environment variables.

---

## 1. Core Application Variables

| Variable Name | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | string | `"COPPER"` | Canonical application name. |
| `APP_VERSION` | string | `"3.0.0"` | SemVer release version. |
| `APP_ENV` | string | `"development"` | Active runtime mode (`"development"`, `"production"`, `"test"`). |
| `ALLOWED_ORIGINS` | JSON list | `["http://localhost:5173", ...]` | Permitted CORS origins for API requests. |

---

## 2. Database & Persistent Storage

| Variable Name | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | string | `"sqlite:///data/copper_memory.db"` | SQLAlchemy connection string. Configures SQLite in WAL mode. |
| `REDIS_URL` | string | `"redis://localhost:6379/0"` | Redis cache connection string (optional; falls back gracefully). |
| `DOCUMENTS_DIR` | string | `"data/documents"` | Directory for user-uploaded documents and indexed knowledge files. |

---

## 3. Local Model & Inference Engine (Ollama)

| Variable Name | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `OLLAMA_BASE_URL` | string | `"http://localhost:11434"` | HTTP API address of the local Ollama instance. |
| `AI_MODELS_DIR` | string | `"ai-models"` | Root path for quantized model files and manifests. |
| `GATEKEEPER_KEEP_ALIVE` | integer | `-1` | Ollama model keep-alive duration in seconds (`-1` keeps always loaded). |
| `HEAVY_MODEL_IDLE_UNLOAD_SECONDS` | integer | `240` | Idle timeout before offloading 14B+ models from VRAM. |

---

## 4. Voice, Audio, & Wake-Word Pipeline

| Variable Name | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `WAKE_WORD_ENGINE` | string | `"openwakeword"` | Acoustic wake-word detector engine. |
| `WAKE_WORD_MODEL_PATH` | string | `"ai-models/wakeword/hey_copper.onnx"` | ONNX acoustic model checkpoint for "Hey COPPER". |
| `TTS_ENGINE` | string | `"auto"` | Text-to-speech engine (`"auto"`, `"local"`, `"edge-tts"`). |
| `TTS_OFFLINE_ONLY` | boolean | `true` | Enforces zero-cloud voice synthesis. |

---

## 5. Local Code Execution Sandbox

| Variable Name | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `SANDBOX_BACKEND` | string | `"auto"` | Isolation engine (`"auto"`, `"pyodide"`, `"docker"`). |
| `SANDBOX_TIMEOUT_SECONDS` | integer | `15` | Maximum execution time before subprocess termination. |
| `SANDBOX_MEMORY_LIMIT_MB` | integer | `256` | Maximum resident memory quota for sandboxed processes. |
| `SANDBOX_CPU_LIMIT` | float | `1.0` | Maximum CPU core quota. |
| `SANDBOX_NETWORK_ENABLED` | boolean | `false` | Complete network isolation for untrusted script execution. |

---

## 6. Observability & OpenTelemetry

| Variable Name | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `OTEL_ENABLED` | boolean | `false` | When `false`, zero telemetry connections are attempted. |
| `OTEL_SERVICE_NAME` | string | `"copper-backend"` | Service identifier in distributed traces. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | string | `"http://localhost:4317"` | gRPC endpoint for external Tempo/Grafana exporter. |
| `GRAFANA_URL` | string | `"http://localhost:3000"` | Local Grafana metrics dashboard address. |

---

## 7. Storage Directory Structure

```text
data/
├── audio/          # Temporary recordings and TTS cache
├── conversations/  # Exported chat transcripts
├── documents/      # User documents indexed for RAG
├── logs/           # Application and security audit logs
│   ├── app/
│   └── security/
├── memory/         # SQLite memory database and fact backups
├── reminders/      # Cron-scheduled event states
├── screenshots/    # Vision tool analysis captures
└── vector/         # ChromaDB persistent vector index
```
