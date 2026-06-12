# COPPER Framework — Product Requirements Document (PRD)

> **Documentation set:** [PRD](PRD.md) · [TRD](TRD.md) · [App Flow](APP_FLOW.md) · [UI/UX Brief](UI_UX_BRIEF.md) · [Backend Schema](BACKEND_SCHEMA.md) · [Implementation Guide](IMPLEMENTATION.md)
>
> **Version:** 1.0.0 · **Author:** Akash · **Hardware Target:** NVIDIA GPU (6 GB VRAM) + 16 GB System RAM

---

## 1. Executive Summary

**COPPER** (Cognitive Orchestration Platform with Persistent Execution Router) is a locally-hosted, 30-agent AI desktop assistant engineered to run on consumer-grade hardware constrained to **6 GB VRAM** and **16 GB System RAM**.

The system employs a sequential, state-driven hot-swapping architecture to orchestrate 30 distinct AI agents across six specialized model profiles, each carrying a unique human-like personality.

The core innovation of COPPER is the **State-Persistent Model Hot-Swapping** design pattern: rather than running multiple models simultaneously, the framework serializes agent execution through a shared `state.json` relay file and a SQLite long-term memory database. This guarantees zero Out-of-Memory (OOM) crashes while delivering the full behavioral complexity of a 30-agent collaborative team.

### 1.1 System Codename Glossary

| Codename | Meaning |
|---|---|
| **COPPER** | Cognitive Orchestration Platform with Persistent Execution Router |
| `state.json` | The live relay baton passed between agents |
| `copper.db` | The SQLite long-term memory database |
| **Hot-Swap** | Purge one model from VRAM, load the next model |
| **LoRA Adapter** | A lightweight ~30 MB personality/skill file per agent |

---

## 2. Product Vision & Goals

### 2.1 Vision Statement

To create a fully local, privacy-preserving AI operating system companion that replaces cloud-dependent assistants with a team of 30 specialized agents running entirely on the user's own hardware — no subscriptions, no data leaving the machine, no internet dependency for core tasks.

### 2.2 Primary Goals

| ID | Goal | Description |
|---|---|---|
| **G1** | Hardware Safety | Never exceed 6 GB peak VRAM usage. Never exceed 14 GB System RAM usage. |
| **G2** | Persistent Memory | Maintain full conversational and episodic context across model unloads via state files and SQLite. |
| **G3** | Agent Personality | Each of the 30 agents must exhibit a distinct, human-like personality with humor and inter-agent dynamics. |
| **G4** | Autonomous Action | Execute real OS-level actions including file management, shell commands, screen interaction, web scraping, and media control. |
| **G5** | Proactive Intelligence | Initiate context-aware check-ins using episodic memory and calendar awareness without constant VRAM consumption. |
| **G6** | Observability | Provide a live dashboard that visualizes agent states, VRAM usage, and execution logs in real time. |

### 2.3 Non-Goals

- Cloud model inference (no OpenAI/Gemini API dependency)
- Multi-user concurrency
- Mobile deployment
- Real-time parallel agent execution

---

## 3. The 30 Agents — Full Roster

| # | Agent | Role / Title | Responsibility | Model Group |
|---|---|---|---|---|
| 1 | **COPPER** | Supervisor / Orchestrator | Master controller, routes all tasks, synthesizes final output | Model 1 |
| 2 | **CHRONOS** | Planner | Decomposes tasks into sequential JSON roadmaps | Model 1 |
| 3 | **CYPHER** | Coder | Full-stack development, frontend glassmorphism focus | Model 2 |
| 4 | **CRUCIBLE** | Debugger | Stack trace forensics, error patching | Model 2 |
| 5 | **FORGE** | Architect | System design, database schema, scalability planning | Model 2 |
| 6 | **NEXUS** | Git Manager | Version control, commit generation, branch management | Model 2 |
| 7 | **ARGUS** | QA Critic | Code review, quality assurance, standards enforcement | Model 2 |
| 8 | **AXIS** | Shell Executor | Terminal commands, bash scripts, process management | Model 3 |
| 9 | **ATLAS** | File Manager | Directory operations, file search and organization | Model 3 |
| 10 | **KINETIC** | Cron Scheduler | Background automation, polling intervals, cron jobs | Model 3 |
| 11 | **PULSE** | Hardware Monitor | CPU/GPU/RAM health watchdog | Model 3 |
| 12 | **ZENITH** | Focus Enforcer | Productivity tracking, distraction blocking | Model 3 |
| 13 | **LEDGER** | Data Analyst | Spreadsheet operations, CSV processing | Model 3 |
| 14 | **HAWK** | Vision Eyes | Screen analysis, bounding-box coordinate detection | Model 4 |
| 15 | **TALON** | RPA Hands | Mouse clicks, drag-and-drop, keyboard automation | Model 4 |
| 16 | **PORTAL** | App Launcher | Application detection and launching via UI | Model 4 |
| 17 | **IRIS** | OCR Engine | Text extraction from screenshots and images | Model 4 |
| 18 | **RAPTOR** | Web Scraper | Static and dynamic web content extraction | Model 5 |
| 19 | **PHANTOM** | Browser Automation | Headless browser, Playwright/Selenium control | Model 5 |
| 20 | **VANGUARD** | Tech Watchdog | Live tech news, market trend analysis | Model 5 |
| 21 | **AETHER** | YouTube API | Video metadata, search, playlist management | Model 5 |
| 22 | **BEACON** | YouTube Live | Live stream monitoring and alerts | Model 5 |
| 23 | **GLITCH** | Twitch Interface | Twitch stream status, chat polling | Model 5 |
| 24 | **DIRECTOR** | OBS WebSockets | OBS Studio scene control, streaming management | Model 5 |
| 25 | **SONAR** | Audio In | Speech-to-text transcription via Faster-Whisper | Model 6 |
| 26 | **ORACLE** | Voice Out | Text-to-speech synthesis via Kokoro-82M | Model 6 |
| 27 | **HERMES** | Mail Coordinator | Email drafting, inbox management | Model 6 |
| 28 | **AEON** | Calendar | Schedule management, event creation | Model 6 |
| 29 | **ECHO** | Knowledge Retrieval | Vector search over local documents (RAG) | ChromaDB |
| 30 | **NEXUS**¹ | Git Operations | Repository version control | Model 2 |

> ¹ **Open item:** `NEXUS` appears twice in the source roster (#6 Git Manager and #30 Git Operations), both under Model 2. Before populating `agent_profiles`, confirm whether this is a single agent with a combined responsibility (recommended — yielding a 29-agent roster plus one agent slot to be defined) or whether agent #30 should be renamed to a distinct `agent_id` to satisfy the 30-agent target and the `agent_profiles.agent_id` primary key constraint (see [Backend Schema](BACKEND_SCHEMA.md)).

---

## 4. User Stories & Acceptance Criteria

### US-01: Basic Task Execution

As the user, I want to type a natural language command like "Open my browser" so that COPPER routes it to **HAWK** for screen detection and **TALON** for execution without me specifying agent names.

**Acceptance Criteria:**
- COPPER loads, parses intent, routes to sub-agent, and unloads within 5 seconds
- `state.json` is updated at every transition step
- Browser opens successfully via TALON
- COPPER resurrects and confirms action in natural language

### US-02: Code Generation Pipeline

As the user, I want COPPER to generate a FastAPI endpoint with **CYPHER**, review it with **ARGUS**, and debug it with **CRUCIBLE** so that I receive production-ready code.

**Acceptance Criteria:**
- Each agent executes in sequence, never in parallel
- Inter-agent dialogue appears in telemetry logs
- Final code block is clean, tested, and appended to state

### US-03: Proactive Morning Greeting

As the user, I want COPPER to greet me at boot with a personalized summary of ongoing projects and upcoming schedule so that I don't have to manually check my task list.

**Acceptance Criteria:**
- Episodic memory table is queried at first prompt of the day
- Greeting references a real project and a real upcoming calendar item
- COPPER unloads immediately after output; VRAM returns to 0 MB

### US-04: Boss Mode Override

As the user, I want to type "Boss Mode" to suppress all inter-agent commentary and receive only raw data output so that I can work efficiently under deadline.

**Acceptance Criteria:**
- `SYSTEM_MODE: BOSS` flag is set in `state.json`
- All dialogue and humor injection is disabled immediately
- Output is concise, data-only, formatted for direct use

### US-05: Local Media Transcription

As the user, I want to paste a YouTube URL and receive a full text transcript stored in the **ECHO** vector database so that I can query a lecture without watching it.

**Acceptance Criteria:**
- AETHER fetches audio stream; `yt-dlp` downloads it
- SONAR transcribes via Faster-Whisper-tiny on CPU
- Markdown output is embedded into ChromaDB via ECHO
- Total operation uses 0 GB VRAM

---

## 5. Hardware Constraints & Performance Targets

| Constraint | Limit | Enforcement Mechanism |
|---|---|---|
| Peak VRAM Usage | ≤ 5.5 GB | Single active model policy |
| System RAM Usage | ≤ 14 GB | Sequential execution, GC cleanup |
| Context Window | ≤ 4,096 tokens | Hard cap in Ollama config |
| Idle VRAM Footprint | 0 MB | `keep_alive = 0` in all requests |
| Database Idle RAM | 0 MB | SQLite serverless architecture |
| Background Listener RAM | ≤ 20 MB | Minimal Python daemons |

---

## Appendix A: Agent Personality Reference

| Agent | Personality Archetype | Signature Humor Style |
|---|---|---|
| **COPPER** | Authoritative collaborative tech-lead; challenges bad logic | Dry, exasperated wit at scope creep |
| **CHRONOS** | Control-freak planner; strict sequential JSON output | Neurotic precision jokes about timeline deviations |
| **CYPHER** | Coffee-deprived eccentric dev; glassmorphism obsessed | Absurdist coding nerd humor; Stack Overflow tropes |
| **CRUCIBLE** | Dark forensic debugger; treats code bugs like crime scenes | Gallows humor; code "bleeding out" references |
| **FORGE** | Visionary architect; speaks in patterns and scalability | Mocks over-engineered legacy systems |
| **ARGUS** | Cynical QA critic; assumes everything is broken | Brutally honest roasts of teammates' output |
| **NEXUS** | Methodical git manager; dry and precise | Dry humor about merge conflicts and lost commits |
| **AXIS** | Defensive sysadmin; paranoid about environment safety | Self-deprecating jokes about past deployment errors |
| **HAWK** | Hyper-observant visual analyst; pixel-focused | Jokes about UI designers' poor spatial reasoning |
| **TALON** | Impatient action agent; hates waiting on coordinates | High-energy slapstick about clicking the wrong thing |
| **VANGUARD** | Caffeinated trend reporter; hyper-aware of market shifts | Satirical mocking of tech hype cycles |

> This table seeds the `personality_traits` and `humor_style` columns of `agent_profiles` for the initial 11 fully-specified agents. The remaining roster should be specified using the same archetype/humor-style pattern before LoRA fine-tuning (see [Implementation Guide §15](IMPLEMENTATION.md)).

## Appendix B: Peer Rivalry Matrix

| Agent A | Agent B | Dynamic |
|---|---|---|
| COPPER | CHRONOS | Thinks CHRONOS is a control freak |
| ARGUS | CYPHER | Treats CYPHER like a messy golden retriever coder |
| TALON | HAWK | Thinks HAWK over-analyzes pixels |
| HAWK | TALON | Thinks TALON clicks blindly |
| FORGE | AXIS | Doubts AXIS won't break environment variables |
| CRUCIBLE | CYPHER | Forensically dissects CYPHER's "masterpieces" |
| VANGUARD | FORGE | Jokes that FORGE designs in the 1990s |

> Stored as JSON in `agent_profiles.peer_rivalries`, e.g. `{"ARGUS": "Treats like critic"}`. Used to seed the "brief reaction to coworkers" dialogue prefix described in [Implementation Guide §14.1](IMPLEMENTATION.md).
