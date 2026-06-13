# COPPER Framework

**Cognitive Orchestration Platform with Persistent Execution Router**

A locally-hosted, 30-agent AI desktop assistant that runs entirely on consumer hardware — **6 GB VRAM / 16 GB System RAM** — using a sequential, state-driven model hot-swapping architecture. No subscriptions, no cloud inference, no data leaving the machine.

> **Status:** v1.0.0 specification · **Author:** Akash · **Deployment:** Local-only, single-user

---

## What is COPPER?

Instead of running multiple LLMs in parallel (which would blow past 6 GB of VRAM instantly), COPPER runs **one model at a time**, hot-swapping between six specialist model profiles via Ollama + llama.cpp. A shared `state.json` relay file and a SQLite database (`copper.db`) preserve full conversational and episodic context across every model unload — guaranteeing **zero OOM crashes** while still delivering the behavior of a 30-agent collaborative team, each with its own personality, humor style, and LoRA adapter.

| Capability | Summary |
|---|---|
| 30 specialized agents | Coding, debugging, OS automation, vision/RPA, web/streaming, audio — see [PRD §3](docs/PRD.md#3-the-30-agents--full-roster) |
| Sequential hot-swap engine | One model in VRAM at a time, `keep_alive: 0`, atomic state relay — see [TRD §6](docs/TRD.md#6-system-architecture-overview) |
| Persistent memory | `state.json` (volatile) + `copper.db` (SQLite, serverless) + ChromaDB (local RAG) — see [Backend Schema](docs/BACKEND_SCHEMA.md) |
| Proactive intelligence | Morning greetings, alarms, calendar, screen-change detection — see [App Flow §8.3–8.4](docs/APP_FLOW.md) |
| Live telemetry dashboard | React + Tailwind, AeroNet-inspired design system — see [UI/UX Brief](docs/UI_UX_BRIEF.md) |

---

## Hardware Requirements

| Requirement | Minimum |
|---|---|
| GPU VRAM | 6 GB (peak usage capped at 5.5 GB) |
| System RAM | 16 GB (capped at 14 GB) |
| OS | Windows / Linux (macOS untested) |
| Internet | Required only for initial model downloads |

Full constraint table: [PRD §5 — Hardware Constraints & Performance Targets](docs/PRD.md#5-hardware-constraints--performance-targets).

---

## Quick Start

```bash
git clone <this-repo>
cd copper_framework
bash docs/setup/setup.sh
python3 engine.py
```

For the full walkthrough (prerequisites, model pulls, database init, daemons, frontend), see **[docs/setup/README.md](docs/setup/README.md)**.

---

## Documentation

All project documentation lives under [`docs/`](docs/README.md). Start there for the full documentation map — Product Requirements, Technical Requirements, Application Flow, UI/UX Brief, Backend Schema, Implementation Guide, plus reference material (API, architecture, diagrams, research, setup).

---

## Project Structure

```
copper_framework/
├── engine.py                  # Main orchestration loop
├── proactive_engine.py        # Morning greeting / check-in generator
├── clock_daemon.py            # Background alarm / reminder watcher
├── kinetic_daemon.py          # Weather & live stream poller
├── screen_diff.py             # Passive vision change detector
├── guardrails.py              # Command whitelist enforcer
├── state.json                 # Live active relay baton
├── copper.db                  # SQLite long-term memory
├── adapters/                   # LoRA personality adapter files
├── chroma_store/               # ChromaDB vector database (ECHO)
├── frontend/                    # React + Tailwind dashboard
├── models/                      # Symlinks to Ollama model paths
├── docs/                         # All project documentation (see below)
└── requirements.txt
```

Full breakdown: [Implementation Guide §13](docs/IMPLEMENTATION.md#13-project-directory-structure).

---

## License

Confidential — Local Deployment Only. License terms to be finalized.
