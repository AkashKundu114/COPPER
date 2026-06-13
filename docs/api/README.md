# API Reference — Local API Surface

> **Documentation hub:** [docs/README.md](../README.md) · **Related:** [App Flow §9](../APP_FLOW.md#9-frontend-dashboard-flow) · [Backend Schema §11](../BACKEND_SCHEMA.md#11-statejson--active-state-schema)

---

## Scope

COPPER has **no external or cloud-facing API**, per [PRD §2.3 Non-Goals](../PRD.md#23-non-goals). Every endpoint described in this document is bound to `127.0.0.1` and reachable only from the local machine. There are two API surfaces:

1. **Ollama Inference API** — between `engine.py` and the locally-running Ollama daemon
2. **Dashboard Bridge API** — between the React frontend and `state.json` / `copper.db`

---

## 1. Ollama Inference API

**Base URL:** `http://localhost:11434`

This is Ollama's own REST API, consumed by `engine.py` exactly as shown in [Implementation Guide §14.1](../IMPLEMENTATION.md#141-main-orchestration-loop). COPPER does not modify or extend this API — documented here for completeness and so frontend/automation developers know it exists on the same host.

### `POST /api/chat`

Used by `run_agent()` to run a single inference turn for the active agent.

| | |
|---|---|
| **Request body** | `{ "model": string, "messages": [{"role": "system"\|"user", "content": string}], "options": {"keep_alive": 0, "num_ctx": 4096} }` |
| **Response** | `{ "message": {"role": "assistant", "content": string}, ... }` |
| **Notes** | `model` is resolved from `MODEL_MAP` (see [Implementation Guide §14.1](../IMPLEMENTATION.md#141-main-orchestration-loop)). `keep_alive: 0` is **mandatory** per [TRD §7.1 TR-01](../TRD.md#71-tr-01-model-lifecycle-management). |

### `POST /api/generate`

Used by `flush_vram()` as a no-op "wake and immediately unload" call to confirm VRAM release.

| | |
|---|---|
| **Request body** | `{ "model": string, "keep_alive": 0, "prompt": "" }` |
| **Response** | Standard Ollama generate response (content ignored) |
| **Notes** | Called after every agent transition — see [App Flow §8.2.3](../APP_FLOW.md#823-step-3--gpu-hard-reset). |

---

## 2. Dashboard Bridge API

**Base URL:** `http://localhost:<bridge-port>/api` (Express.js — exact port is a deployment detail, document in [setup/README.md](../setup/README.md) once finalized)

This thin Express.js layer exists **only** to let the browser-sandboxed React frontend read/write local files (`state.json`) and query `copper.db`, which it cannot do directly. It performs no business logic — `engine.py` remains the sole writer of orchestration state.

> **Open item:** This API is implied by [App Flow §9](../APP_FLOW.md#9-frontend-dashboard-flow) ("polls `state.json` every 300 milliseconds via a local Express.js bridge API") but its concrete endpoint shapes are not yet specified in the core docs. The endpoints below are a proposed contract consistent with the [Backend Schema](../BACKEND_SCHEMA.md) and [UI/UX Brief](../UI_UX_BRIEF.md) — confirm against the actual `frontend/api/statePoller.js` implementation ([Implementation Guide §13](../IMPLEMENTATION.md#13-project-directory-structure)) and update this table accordingly.

### `GET /api/state`

Returns the current contents of `state.json` for the dashboard poller.

| | |
|---|---|
| **Response** | Full [`state.json` schema](../BACKEND_SCHEMA.md#11-statejson--active-state-schema) as JSON |
| **Consumed by** | Pulse Badge, Action Banner, VRAM Gauge, Dialogue Log, System Log — [UI/UX Brief §3](../UI_UX_BRIEF.md#3-component-specifications) |
| **Polling interval** | 300ms — [App Flow §9](../APP_FLOW.md#9-frontend-dashboard-flow) |

### `POST /api/prompt`

Submits a new user prompt, equivalent to [App Flow §8.2.1, Step 1](../APP_FLOW.md#821-step-1--user-input-ingestion).

| | |
|---|---|
| **Request body** | `{ "prompt": string }` |
| **Effect** | Writes `user_prompt`, sets `next_agent = "COPPER"`, `system_status = "PROCESSING"` in `state.json` |
| **Consumed by** | Prompt Input — [UI/UX Brief §3.6](../UI_UX_BRIEF.md#36-prompt-input) |

### `POST /api/confirm`

Resolves a pending Confirmation Modal for TALON/AXIS destructive actions ([TRD §7.6](../TRD.md#76-tr-06-security-guardrails-axis--talon)).

| | |
|---|---|
| **Request body** | `{ "approved": boolean }` |
| **Effect** | Writes the user's `Y`/`N` decision into `task_context`, unblocking the waiting agent |
| **Consumed by** | Confirmation Modal — [UI/UX Brief §3.7](../UI_UX_BRIEF.md#37-confirmation-modal) |

### `GET /api/history`

Returns recent chat history for a session.

| | |
|---|---|
| **Query params** | `session_id` (string, required) |
| **Response** | Array of rows from `chat_history` — [Backend Schema §12.2](../BACKEND_SCHEMA.md#122-chat-history-table) |

### `GET /api/episodes`

Returns recent episodic memory entries, used to render "what COPPER will mention next time it greets you" in a settings/debug view.

| | |
|---|---|
| **Response** | Array of rows from `episodic_memory`, ordered by `last_activity_date DESC` — [Backend Schema §12.5](../BACKEND_SCHEMA.md#125-episodic-memory-table) |
| **Notes** | Mirrors the query used by `generate_proactive_context()` — [Implementation Guide §14.3](../IMPLEMENTATION.md#143-proactive-engine) |

---

## 3. ChromaDB (Local Vector Store)

ChromaDB runs in **embedded/local mode** as part of the ECHO agent's process — it does not expose an HTTP server and is not part of the "API surface" in the network sense. Documented here only to make explicit that it is **not** a remote service: see [research/architecture-alternatives.md](../research/architecture-alternatives.md) for why a server-mode vector DB was rejected.

---

## Security Notes

- All endpoints above are bound to `127.0.0.1` / `localhost` only. There is no authentication layer because there is no network exposure — do **not** bind the Express.js bridge to `0.0.0.0` without re-evaluating this entire section.
- The Dashboard Bridge API has write access to `state.json` only for the two narrow purposes above (prompt submission, confirmation response). It must never be given a generic "write arbitrary JSON to state.json" endpoint, as that would bypass the atomic-write and validation guarantees in [TRD §7.4 TR-04](../TRD.md#74-tr-04-state-file-integrity).
