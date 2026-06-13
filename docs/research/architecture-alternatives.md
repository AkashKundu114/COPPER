# Architecture Alternatives Considered

> **Documentation hub:** [docs/README.md](../README.md) · **Research index:** [research/README.md](README.md) · **Adopted architecture:** [architecture/architecture.md](../architecture/architecture.md)
>
> **Status:** Deprecated / Not Adopted — preserved for historical traceability only.

---

## Why this document exists

An early architecture draft for COPPER described a **cloud-hybrid, server-based stack**. It is reproduced below, unedited, followed by a section explaining why it was not adopted in favor of the local-only, sequential hot-swap architecture in [architecture/architecture.md](../architecture/architecture.md).

This document should **not** be used as current guidance. It exists so that:

1. The reasoning behind the current architecture is auditable rather than assumed.
2. If a future "COPPER Cloud" or multi-user variant is ever scoped, this is the starting point — but it would require revisiting [PRD §2.3 Non-Goals](../PRD.md#23-non-goals) and [PRD §2.2 G1](../PRD.md#22-primary-goals) as a product decision first, not a silent architecture drift.

---

## Original Draft (Verbatim)

> **Source:** `docs/architecture/architecture.md`, pre-v1.0.0

### Overview

COPPER follows a modular AI-driven desktop assistant architecture.

The system consists of:

1. Frontend Layer
2. AI Backend Layer
3. Automation Layer
4. Database Layer
5. Infrastructure Layer

### Frontend Layer

**Technologies:** React, Tailwind CSS, Framer Motion, Tauri

**Responsibilities:** Dashboard UI, Chat UI, Voice visualization, Notifications, Settings management

### AI Backend Layer

**Technologies:** FastAPI, LangChain, Ollama, OpenAI APIs

**Responsibilities:** AI orchestration, Prompt management, Agent routing, Memory processing, Context handling

### Automation Layer

**Technologies:** Python, PowerShell, AutoHotkey

**Responsibilities:** Desktop automation, App launching, File management, Workflow execution

### Database Layer

**Technologies:** PostgreSQL, ChromaDB, Redis

**Responsibilities:** User data, AI memory, Vector embeddings, Chat history, Caching

### Infrastructure Layer

**Technologies:** Docker, Docker Compose, GitHub Actions

**Responsibilities:** Deployment, CI/CD, Container orchestration, Service isolation

---

## Why This Was Not Adopted

| Element in original draft | Conflicts with | Resolution in adopted architecture |
|---|---|---|
| **OpenAI APIs** in AI Backend Layer | [PRD §2.3 Non-Goals](../PRD.md#23-non-goals): *"Cloud model inference (no OpenAI/Gemini API dependency)"* | Inference is local-only via Ollama + llama.cpp ([architecture.md §2](../architecture/architecture.md#2-orchestration-layer-ai-core)) |
| **FastAPI** as an always-on backend server | [TRD §6.1 Core Invariant](../TRD.md#61-architecture-pattern-sequential-hot-swap-engine): single sequential Python loop, no server process | Replaced by `engine.py`'s sequential orchestration loop + a thin local Express.js bridge for the dashboard only |
| **LangChain** for orchestration | [TRD §6.1](../TRD.md#61-architecture-pattern-sequential-hot-swap-engine) and [TRD §7.3 TR-03](../TRD.md#73-tr-03-sequential-execution): orchestration must be explicit sequential `for` loops, never framework-managed parallel/async chains | Replaced by the explicit `run()` loop in [Implementation Guide §14.1](../IMPLEMENTATION.md#141-main-orchestration-loop) |
| **PostgreSQL** in Database Layer | [PRD §5](../PRD.md#5-hardware-constraints--performance-targets): *"Database Idle RAM: 0 MB ... SQLite serverless architecture"* | Replaced by SQLite (`copper.db`) — see [Backend Schema §12](../BACKEND_SCHEMA.md#12-sqlite-database-schema-copperdb) |
| **Redis** for caching | Same as above — any always-on server process violates the 0 MB idle-RAM target and the "single active model / minimal daemons" hardware safety goal (G1) | No caching layer; `state.json` serves as the volatile relay, `copper.db` as persistent storage |
| **Docker / Docker Compose** for deployment | [PRD title block](../../README.md): *"Confidential – Local Deployment Only"*; containerization adds RAM/CPU overhead and complicates the GPU passthrough required for Ollama on consumer hardware | Local Python venv + `pip install -r requirements.txt` + native Ollama install — see [setup/README.md](../setup/README.md) |
| **PowerShell / AutoHotkey** as primary automation stack | [Implementation Guide §16.1](../IMPLEMENTATION.md#161-prerequisites) specifies a Python-first, cross-platform automation stack (`pyautogui`, OpenCV, Playwright) | Python automation stack is primary; platform-specific scripting may be added as optional backends (see [architecture.md §3](../architecture/architecture.md#3-automation-layer)) |

### What was kept

A few elements from the original draft remain valid and are carried forward:

- **React + Tailwind CSS + Framer Motion** for the frontend (now themed per the [UI/UX Brief](../UI_UX_BRIEF.md))
- **ChromaDB** for vector embeddings (now specified as local/embedded, not a server)
- **GitHub Actions** — retained, but scoped to linting/tests rather than container deployment
- **Tauri** as an optional desktop packaging shell — does not introduce a network dependency

---

## Open Question for Future Consideration

If COPPER ever needs to support **multiple users or remote access** (explicitly out of scope per [PRD §2.3](../PRD.md#23-non-goals): *"Multi-user concurrency"*), the original draft's server-based stack (FastAPI + PostgreSQL + Redis + Docker) would be a more appropriate starting point than the current local-relay design. This would be a **major version** change (v2.0) and should be tracked as a product decision, not introduced incrementally into the v1.x local architecture.
