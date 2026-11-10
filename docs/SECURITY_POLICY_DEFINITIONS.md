# C.O.P.P.E.R. Security Policy Definitions

This document formally specifies the active authorization rules, permission mappings, and operational security boundaries for C.O.P.P.E.R.

---

## 1. Role-Based Access Control (RBAC) Specification

| Role | Permitted Actions | Excluded Actions | Primary Use Case |
| :--- | :--- | :--- | :--- |
| **`ADMIN`** | Full access to all endpoints, tools, memories, and configuration settings. | None (subject to ABAC operator confirmation). | Host workstation operator managing system configuration. |
| **`OPERATOR`** | Execute safe and moderate tools, activate agents, chat, read/export audit logs, manage memories. | Audit purge (`audit:delete`), direct arbitrary shell execution without confirmation. | Standard everyday human operator interaction. |
| **`AGENT`** | Execute authorized agent-scoped tools, read memories, generate chat completions. | Administrative endpoints, system configuration, unauthorized tools. | Autonomous internal agent execution contexts. |
| **`AUDITOR`** | Read system telemetry, inspect audit trail, download compliance data export. | All tool execution, memory write, agent activation. | External compliance review or security auditing. |
| **`READ_ONLY`** | Read system status, health checks, public cockpit telemetry. | All state mutations, all tool invocations, chat interaction. | Public status dashboards or read-only monitoring. |

---

## 2. Tool Guardian & Capability Level Classification

Every registered tool is bound to a strict Guardian Level and Permission Category:

| Tool Name | Guardian Level | Required Permission | Default Execution Environment |
| :--- | :---: | :--- | :--- |
| `file_read` | L0 (Safe) | `tool:execute:safe` | Local filesystem (workspace roots only) |
| `calendar_list` | L0 (Safe) | `tool:execute:safe` | In-memory / local SQLite |
| `memory_search` | L0 (Safe) | `tool:execute:safe` | ChromaDB vector store |
| `web_search` | L1 (Moderate) | `tool:execute:moderate` | SearXNG / DuckDuckGo (redacted) |
| `web_fetch` | L1 (Moderate) | `tool:execute:moderate` | HTTP client with SSRF filter |
| `memory_store` | L1 (Moderate) | `tool:execute:moderate` | MemoryQuarantine evaluation |
| `python_execute` | L2 (Sensitive) | `tool:execute:sensitive` | Forge Sandbox (Docker/WASM/JobObject) |
| `file_write` | L2 (Sensitive) | `tool:execute:sensitive` | Local workspace (restricted roots) |
| `git_commit` | L2 (Sensitive) | `tool:execute:sensitive` | Host git repository |
| `shell_execute` | L3 (Critical) | `tool:execute:critical` | Host OS shell (Operator Confirmation Required) |
| `file_delete` | L3 (Critical) | `tool:execute:critical` | Workspace (Operator Confirmation Required) |

---

## 3. Network Isolation Policy Rules

1. **`OFFLINE_AIRGAP`:**
   - Outbound WAN connections: **PROHIBITED**
   - Outbound loopback connections: **PROHIBITED**
   - Web Search: Disabled
   - Model Inference: Local Ollama daemon only
2. **`LOCAL_SERVICES`:**
   - Outbound WAN connections: **PROHIBITED**
   - Outbound loopback connections: **PERMITTED** (`127.0.0.1`, `localhost` only)
   - Permitted Endpoints: SearXNG (`http://localhost:8888`), Ollama (`http://localhost:11434`), Redis (`localhost:6379`), PostgreSQL (`localhost:5432`)
3. **`USER_AUTHORIZED_EGRESS`:**
   - Outbound WAN connections: **PERMITTED**
   - Cloud Metadata (`169.254.169.254`): **BLOCKED**
   - Private RFC 1918 Subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`): **BLOCKED** (SSRF defense)
   - Data Sanitization: All outbound strings masked via `DataFirewall.redact()`

---

## 4. Secret Isolation Policy Rules

1. Secrets must be registered in `SecretVault` and never hardcoded in source code or `.env` templates.
2. Any secret registered with `SecretVault` is dynamically added to `DataFirewall._PATTERNS`.
3. If an agent attempts to emit a vault secret, it is replaced with `•••VAULT_SECRET_REDACTED•••`.
4. Stored secrets are excluded from database backups and client telemetry exports.
