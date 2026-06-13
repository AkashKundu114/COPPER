# COPPER Architecture

> **Documentation hub:** [docs/README.md](../README.md) · **Index:** [architecture/README.md](README.md) · **Related:** [TRD §6](../TRD.md#6-system-architecture-overview) · [PRD §2](../PRD.md#2-product-vision--goals)
>
> **Revision note:** This document was rewritten to align with [TRD §6](../TRD.md#6-system-architecture-overview) and [PRD §2.3 Non-Goals](../PRD.md#23-non-goals). A previous draft describing a cloud-hybrid, server-based stack is preserved at [research/architecture-alternatives.md](../research/architecture-alternatives.md) — see [architecture/README.md](README.md#️-revision-note) for why it was not adopted.

---

## Overview

COPPER follows a **modular, locally-deployed AI desktop assistant architecture**. Unlike a typical client-server SaaS application, COPPER has **no backend server process** — the "backend" is a Python orchestration loop that runs on the same machine as the frontend, talking to a local-only Ollama instance and a serverless SQLite database.

The system consists of seven layers:

1. [Frontend Layer](#1-frontend-layer)
2. [Orchestration Layer](#2-orchestration-layer-ai-core)
3. [Automation Layer](#3-automation-layer)
4. [Data Layer](#4-data-layer)
5. [Background Services Layer](#5-background-services-layer)
6. [Audio I/O Layer](#6-audio-io-layer)
7. [Tooling & Dev Layer](#7-tooling--dev-layer)

---

## 1. Frontend Layer

**Technologies:** React, Tailwind CSS, Framer Motion, Express.js (local bridge), optionally Tauri for desktop packaging.

**Responsibilities:**

- Dashboard UI (Pulse Badge, Action Banner, VRAM Gauge, Dialogue Log, System Log) — see [UI/UX Brief §3](../UI_UX_BRIEF.md#3-component-specifications)
- Prompt Input (glassmorphism overlay, `Alt+Space` hotkey)
- Confirmation Modal for TALON/AXIS destructive actions
- Polling `state.json` every 300ms via the local Express.js bridge — see [App Flow §9](../APP_FLOW.md#9-frontend-dashboard-flow) and [API Reference](../api/README.md)

> **Note:** Tauri (or an Electron equivalent) is optional and purely for desktop packaging/window management — it introduces no network dependency and does not affect the hardware envelope in [PRD §5](../PRD.md#5-hardware-constraints--performance-targets).

---

## 2. Orchestration Layer (AI Core)

**Technologies:** Python 3.11+, Ollama + llama.cpp.

**Responsibilities:**

- Sequential hot-swap orchestration loop (`engine.py`) — see [TRD §6.1](../TRD.md#61-architecture-pattern-sequential-hot-swap-engine) and [Implementation Guide §14.1](../IMPLEMENTATION.md#141-main-orchestration-loop)
- Agent routing via `next_agent` / `next_model` in `state.json`
- System prompt assembly from `agent_profiles` (personality, humor, vocabulary, peer rivalries)
- Context compression to stay under the 2,048-token inter-agent budget — see [TRD §7.2](../TRD.md#72-tr-02-context-window-enforcement)
- VRAM lifecycle management (`flush_vram()`, `keep_alive: 0`) — see [TRD §7.1](../TRD.md#71-tr-01-model-lifecycle-management)

> There is **no LangChain, no FastAPI server, and no cloud LLM API** in this layer. All inference is local, sequential, and routed through Ollama's REST API on `localhost:11434`.

---

## 3. Automation Layer

**Technologies:** Python, `pyautogui`, OpenCV, Playwright, `pyperclip`, `pygetwindow` / Xlib, `yt-dlp`, APScheduler.

**Responsibilities:**

- Desktop automation and RPA (TALON, AXIS, ATLAS, PORTAL)
- Application launching and window/workspace awareness
- Headless browser automation (PHANTOM)
- Web scraping and media metadata retrieval (RAPTOR, AETHER, BEACON, GLITCH, DIRECTOR)
- Shared clipboard context injection
- Command safety validation via `guardrails.py` — see [Implementation Guide §14.2](../IMPLEMENTATION.md#142-vram-flush-utility) and [TRD §7.6](../TRD.md#76-tr-06-security-guardrails-axis--talon)

> **Platform note:** The cross-platform tooling above (`pyautogui`, `pygetwindow`/Xlib) covers Windows and Linux. Platform-specific extensions (e.g. AutoHotkey on Windows, `xdotool` on Linux) may be added as optional backends for TALON/AXIS without changing this layer's contract — any such addition should be documented in [research/](../research/README.md).

---

## 4. Data Layer

**Technologies:** `state.json` (flat file), SQLite (`copper.db`), ChromaDB (embedded/local mode).

**Responsibilities:**

| Store | Role | RAM when idle |
|---|---|---|
| `state.json` | Volatile relay baton between agents — [Backend Schema §11](../BACKEND_SCHEMA.md#11-statejson--active-state-schema) | N/A (SSD-resident) |
| `copper.db` (SQLite) | Persistent memory: sessions, chat history, execution logs, agent profiles, episodic memory, temporal tasks — [Backend Schema §12](../BACKEND_SCHEMA.md#12-sqlite-database-schema-copperdb) | 0 MB (serverless) |
| ChromaDB | Vector embeddings for ECHO's RAG over local documents | On-demand only |

> **No PostgreSQL, no Redis.** Both require a long-running server process, which conflicts with the **0 MB Database Idle RAM** target in [PRD §5](../PRD.md#5-hardware-constraints--performance-targets) and the serverless architecture invariant. SQLite and ChromaDB's embedded mode satisfy the same structured-storage and vector-search needs without a daemon.

---

## 5. Background Services Layer

**Technologies:** Python daemons, `watchdog` (inotify-based file watching), APScheduler, Porcupine/Rustpotter (wake-word).

**Responsibilities:**

| Daemon | Purpose | RAM limit |
|---|---|---|
| `clock_daemon.py` | Polls `temporal_tasks` every 60s, fires alarms/reminders — [Implementation Guide §14.4](../IMPLEMENTATION.md#144-clock-daemon) | ≤ 15 MB |
| `kinetic_daemon.py` | Weather polling (30 min), Twitch/YouTube live polling (default 5 min) | ≤ 20 MB |
| `screen_diff.py` | OpenCV pixel-diff every 5s for passive vision triggers — [App Flow §8.4](../APP_FLOW.md#84-passive-vision-flow-screen-change-detection) | ≤ 40 MB |
| Wake-word listener | "Hey COPPER" always-on detection | ≤ 20 MB |

Full requirements: [TRD §7.7](../TRD.md#77-tr-07-background-daemon-requirements).

---

## 6. Audio I/O Layer

**Technologies:** Faster-Whisper-tiny (STT), Kokoro-82M (TTS) — both **CPU-only / ONNX**, no VRAM footprint.

**Responsibilities:**

- SONAR: speech-to-text transcription
- ORACLE: text-to-speech synthesis for proactive announcements and interrupt alerts

This layer is intentionally isolated from the GPU-bound Model 1–5 profiles ([TRD §6.2 — Model 6](../TRD.md#62-the-6-model-specialist-architecture)) so that audio I/O never competes for VRAM.

---

## 7. Tooling & Dev Layer

**Technologies:** Unsloth + QLoRA + TRL (offline, cloud GPU), pip/venv, GitHub Actions (CI for linting/tests only).

**Responsibilities:**

- Personality LoRA adapter fine-tuning — [Implementation Guide §15](../IMPLEMENTATION.md#15-fine-tuning-pipeline) (explicitly a **cloud/offline, dev-time** activity, not part of the runtime — see [Implementation Phases, Phase 8](../IMPLEMENTATION.md#17-implementation-phases))
- Dependency management via `requirements.txt` and `pip install --break-system-packages` where applicable
- CI runs linting and unit tests only — **no containerized deployment pipeline**, since COPPER is single-machine, local-only software (Docker/Docker Compose are not part of the runtime stack)

---

## Layer Interaction Summary

The only thing that crosses layer boundaries on every single user turn is `state.json`. Every layer either reads it, writes it, or both:

- **Frontend** reads it (for telemetry) and writes to it (Prompt Input, Confirmation Modal)
- **Orchestration** reads and writes it on every hot-swap step
- **Automation** agents read their `task_context` and write results back
- **Data Layer** is where `state.json` *is* (plus the durable `copper.db`/ChromaDB stores it rotates into)
- **Background Services** write interrupt payloads directly to `state.json`

This single-relay-file design is what makes the sequential hot-swap pattern work without a message broker, server process, or shared memory — see [TRD §6.1](../TRD.md#61-architecture-pattern-sequential-hot-swap-engine) for the formal invariant.
