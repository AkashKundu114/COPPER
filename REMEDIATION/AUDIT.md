# COPPER Architecture, Security & Codebase Audit (Phase A)

**Audit Date:** October 17, 2026  
**Auditor:** Orchestrator (Subagent R)  
**Target Repository:** `github.com/AkashKundu114/COPPER`  
**Branch:** `release/public-cleanup`  
**Commit Baseline:** `8f17d2b`  

---

## 1. Executive Summary

This comprehensive audit inspects the full repository tree, source code metrics, dependency vulnerabilities, secrets, privacy hygiene, container infrastructure, desktop architecture, and factual claims in the documentation for **C.O.P.P.E.R.** (Centralized Omnifunctional Personal Productivity and Execution Routine).

The project is an alpha-stage personal AI desktop application featuring a FastAPI async backend, an Electron desktop wrapper with React 19 UI, local language-model routing via Ollama, an epistemic decaying memory engine with ChromaDB vector search, and a 4-tier Guardian safety engine.

---

## 2. Repository Tree & Language Breakdown

### 2.1 Language Breakdown & Lines of Code (Source Analysis)

Measured from repository source files (excluding `.git`, `node_modules`, `dist`, `.pytest_cache`, `.ruff_cache`):

| Language / File Format | File Count | Total Lines | Blank Lines | Comment Lines | Executable Code Lines |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Python (`.py`)** | 353 | 62,948 | 9,504 | 1,949 | 51,495 |
| **TypeScript / TSX (`.ts`, `.tsx`)** | 95 | 26,113 | 1,937 | 268 | 23,908 |
| **JavaScript / JSX (`.js`, `.jsx`, `.cjs`, `.mjs`)** | 235 | 5,232 | 185 | 73 | 4,974 |
| **Markdown Documentation (`.md`)** | 97 | 22,610 | 2,750 | 1,792 | 18,068 |
| **JSON Specifications (`.json`, `.jsonl`)** | 236 | 2,662,116 | 10 | 4 | 2,662,102 |
| **YAML / Config (`.yml`, `.yaml`)** | 28 | 3,083 | 260 | 103 | 2,720 |
| **HTML / CSS (`.html`, `.css`)** | 75 | 146,607 | 3,791 | 4,306 | 138,510 |
| **Shell Scripts (`.sh`, `.ps1`, `.bat`)** | 13 | 586 | 61 | 70 | 455 |
| **SQL (`.sql`)** | 1 | 16 | 2 | 3 | 11 |

*Note:* `backend/data/agency_agents_full_catalog.json` and research datasets account for the large line count in JSON format.

### 2.2 Large Files (> 1 MB) Audit

| Path | Size (Bytes) | Git Status | Description & Disposition |
| :--- | :--- | :--- | :--- |
| `backend/data/agency_agents_full_catalog.json` | 1,230,028 (1.23 MB) | **Tracked** | Full catalog of specialized agent personas. Legitimate text dataset. |
| `ai-models/image/sd_turbo.safetensors` | 5,214,561,328 (5.2 GB) | **Ignored** | Local diffusion image model weights. Excluded via `.gitignore`. |
| `ai-models/audio/whisper/ggml-large-v3-turbo.bin` | 874,188,075 (874 MB) | **Ignored** | Whisper STT neural model weights. Excluded via `.gitignore`. |
| `ai-models/audio/tts/kokoro-v0_19.onnx` | 325,525,180 (325 MB) | **Ignored** | Kokoro TTS neural synthesis weights. Excluded via `.gitignore`. |
| `ai-models/audio/whisper/ggml-tiny.en.bin` | 77,704,715 (77 MB) | **Ignored** | Whisper fallback STT weights. Excluded via `.gitignore`. |
| `ai-models/audio/tts/en_US-amy-medium.onnx` | 63,201,294 (63 MB) | **Ignored** | Piper fallback voice model. Excluded via `.gitignore`. |
| `ai-models/audio/tts/en_US-ryan-medium.onnx` | 63,201,294 (63 MB) | **Ignored** | Piper fallback voice model. Excluded via `.gitignore`. |
| `ai-models/audio/tts/voices.bin` | 5,758,648 (5.7 MB) | **Ignored** | Kokoro multi-speaker voice embeddings. Excluded via `.gitignore`. |
| `ai-models/audio/vad/silero_vad.onnx` | 2,327,524 (2.3 MB) | **Ignored** | Silero VAD voice activity detection weights. Excluded via `.gitignore`. |
| `ai-models/wakeword/embedding_model.onnx` | 1,326,578 (1.3 MB) | **Ignored** | OpenWakeWord base audio feature embedding network. Excluded via `.gitignore`. |
| `ai-models/wakeword/hey_copper.onnx` | 1,271,370 (1.27 MB) | **Ignored** | "Hey COPPER" acoustic wake-word classification model. Excluded via `.gitignore`. |

*Finding:* No binary model weights are tracked in Git. Only 1 text JSON catalog exceeds 1 MB.

### 2.3 Database & State Files

| Path | Size | Git Status | Disposition |
| :--- | :--- | :--- | :--- |
| `data/copper_memory.db` | 0 bytes | **Ignored** | SQLite database file created on first run. Excluded by `*.db` in `.gitignore`. |
| `backend/app/ai/ambient/ambient_history.db` | 5.0 MB | **Ignored** | Local ambient sensor history database. Excluded by `*.db` in `.gitignore`. |
| `backend/data/chroma/chroma.sqlite3` | 13.2 MB | **Ignored** | Local ChromaDB vector database. Excluded by `*.sqlite3` in `.gitignore`. |

*Finding:* Zero database files are committed in Git history.

---

## 3. Secrets & Privacy Audit

### 3.1 Working Tree Secrets Scan

A regex scan covering API keys, private keys, JWTs, database URLs, and auth tokens found:
1. **Synthetic Test Secrets:** `tests/core/test_data_firewall.py` and `tests/security/test_ai_red_team.py` contain synthetic dummy test strings (e.g. `sk-1234567890abcdef1234567890abcdef`, `ghp_12345...`) specifically used to assert that the Data Firewall and Guardian red-team tests redact credentials properly. These are safely allowlisted in `.gitleaks.toml`.
2. **Kubernetes Template:** `infrastructure/kubernetes/deployments/copper-full-deployment.yaml:23` contains placeholder `SECRET_KEY: "CHANGE_ME_64_CHAR_HEX"`.
3. **No Live Production Secrets:** Zero active or valid cloud/LLM API keys exist in the repository.

### 3.2 Git History Secrets Scan

A scan across all 247 commits in the git history verified:
- No real third-party API keys (OpenAI, Anthropic, AWS, GitHub) have been committed.
- Commit `dd99ee4` and `7e98f54` added adversarial red-team test fixtures and regex patterns into `test_data_firewall.py` and `guardian.py`.

### 3.3 Privacy & Personal Information (PII) Audit

| Item | Location | Finding | Required Remediation |
| :--- | :--- | :--- | :--- |
| **Personal Profile Data** | `data/user_profile.json` | Contains developer name "Akash Kundu", workstation hardware specs (RTX 5060, AMD 8940HX). | Replace with seeded generic demo profile (`John Doe`, `Software Engineer`, generic system specs) or remove from default repo state. |
| **Author Contact** | `frontend/package.json:5` | Contains author email `akashkundu1152@gmail.com`. | Retain open-source maintainer metadata or generalize to project contact. |
| **Local Path Residue** | Uncommitted local databases | Temporary ChromaDB and ambient SQLite files contain developer machine paths (`/home/akash`, `C:\Users\Akash`). | These files are uncommitted and ignored by `.gitignore`. Clean local scratch state. |

---

## 4. Desktop Framework Reality: Electron vs. Tauri

The repository prompt initially hypothesized a Tauri desktop shell (`src-tauri/`). Audit of the codebase and Git history reveals:

1. **Commit History:** In commit `f76370e` (Aug 12, 2026), a basic `src-tauri` scaffold was introduced. In commit `afb4fdd` (Aug 22, 2026), `src-tauri` was completely removed when the project pivoted to **Electron**.
2. **Current Implementation:**
   - **Electron Version:** 44.0.0 (`frontend/package.json`)
   - **Main Process:** `frontend/electron-main.cjs`
   - **Preload Script:** `frontend/preload.cjs`
   - **Launcher:** `frontend/launch-desktop.js`
   - **Packager:** `electron-builder` 26.15.3 configured for Windows (NSIS), macOS (DMG), and Linux (AppImage/deb).
3. **Security Configuration in `electron-main.cjs`:**
   - `contextIsolation: true` (verified)
   - `nodeIntegration: false` (verified)
   - `sandbox: true` (verified)
   - `webSecurity: true` (verified)
   - Explicit IPC whitelist in `preload.cjs` with `ipcRenderer.invoke` channels (`system:get-status`, `window:minimize`, etc.).
4. **Resolution:** Tauri is marked as **SUPERSEDED / PROTOTYPE REMOVED**. All documentation must honestly describe the desktop shell as **Electron 44 + React 19**.

---

## 5. Storage Engine Design: SQLite vs. PostgreSQL

The repository contains references to both SQLite and PostgreSQL. The actual code implementation was verified in `backend/app/database/postgres.py` and `backend/app/core/config.py`:

1. **Default Mode (Zero-Config Desktop):**
   - Uses **SQLite with Write-Ahead Logging (WAL)**: `data/copper_memory.db`.
   - `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL` enforced automatically on connection.
   - Requires zero external database server or Docker container.
2. **Enterprise / Container Mode (Optional):**
   - Configurable via `DATABASE_URL=postgresql://...`.
   - Connection pooling (`pool_size=20`, `pool_recycle=300`, `pool_pre_ping=True`).
3. **Table Models (14 Total):**
   1. `agent_registry`
   2. `audit_log`
   3. `campaign`
   4. `episode`
   5. `history`
   6. `knowledge_graph`
   7. `lora_adapter`
   8. `memory_v2` (UserMemoryV2)
   9. `project`
   10. `response_evaluation`
   11. `schedule_event`
   12. `self_memory`
   13. `task`
   14. `workspace`
4. **Alembic Migrations:**
   - 4 migration revisions in `backend/alembic/versions/`: `0001_initial`, `0002_guardian_agents_audit`, `0003_self_memory`, `0004_productivity_tasks_projects_events`.
   - Tested and verified: cleanly initializes all 14 tables from scratch on a clean database (`alembic upgrade head` returncode 0).

---

## 6. Feature Status Matrix

| Major Subsystem | Implemented / Partial / Stub | Primary Implementation Files | Test Coverage & Verification |
| :--- | :--- | :--- | :--- |
| **Local LLM Routing** | **Implemented** | `backend/app/ai/orchestration/agent_router.py`, `backend/app/ai/llm/ollama_client.py` | 12 core agents mapped in `AgentType` enum; tested in `tests/core/test_routing.py` |
| **Epistemic Memory Engine** | **Implemented** | `backend/app/ai/memory/memory_manager.py`, `backend/app/ai/memory/vector_store.py` | Confidence thresholds (0.85 Fact / 0.50 Obs / 0.10 Hyp); tested in `tests/memory/test_memory_v2.py` |
| **ChromaDB Vector Retrieval** | **Implemented** | `backend/app/ai/memory/vector_store.py`, `backend/app/ai/memory/reranker.py` | Local in-process embeddings via nomic-embed-text; cross-encoder reranking |
| **Guardian Safety Gatekeeper** | **Implemented** | `backend/app/core/guardian.py`, `backend/app/services/guardian_service.py` | 4 levels (0: EXECUTE, 1: SUGGEST, 2: CHALLENGE, 3: SAFETY); tested in `tests/security/` |
| **Data Firewall & PII Redaction** | **Implemented** | `backend/app/core/data_firewall.py` | High-throughput regex masking; tested in `tests/core/test_data_firewall.py` |
| **AST Code Safety Sandbox** | **Implemented** | `backend/app/core/ast_validator.py`, `backend/app/core/forge_sandbox.py` | Static AST analysis + process sandboxing; tested in `tests/core/test_forge_sandbox.py` |
| **Voice & Ambient Audio** | **Implemented** | `backend/app/ai/ambient/`, `backend/app/ai/voice/` | Whisper Large v3 Turbo STT, Kokoro TTS, OpenWakeWord acoustic model; fallback stub if audio device absent |
| **Electron Desktop Shell** | **Implemented** | `frontend/electron-main.cjs`, `frontend/preload.cjs` | Context isolation, zero node integration in renderer, NSIS/DMG build targets |
| **React 19 Cyber-HUD UI** | **Implemented** | `frontend/src/` (85 components/pages) | 16 sidebar navigation views, D3 neural brain graph, dark theme |
| **Autonomous Swarm Swarming** | **Planned (Roadmap)** | `frontend/src/constants/agents.ts` (`PLANNED_AGENTS`) | `orchestrator`, `evaluator`, `behavior`, `nutrition`, `voice` defined as roadmap targets |

---

## 7. Infrastructure & Container Inventory

| File | Services | Default Ports | Healthchecks | Volume Mounts | Security Posture |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `docker-compose.yml` (Dev/Core) | `backend`, `frontend`, `ollama` | `8000:8000`, `5173:5173`, `11434:11434` | Healthcheck on `backend` (`/health`) and `frontend` | `./data:/app/data`, `ollama_data` | Non-root backend user needed for production hardening; ports should bind to `127.0.0.1` |
| `docker-compose.prod.yml` (Prod/Full) | `backend`, `frontend`, `postgres`, `redis`, `chromadb`, `caddy`, `prometheus`, `grafana` | `80:80`, `443:443`, internal service ports | Configured across services | Named volumes for persistence | Defaults require `.env` generation (no hardcoded passwords permitted in release) |

---

## 8. Quality & Test Inventory

- **Backend Pytest Suite:** 676 passing tests across 87 test modules (0 failures, 2 benign warnings in 185s).
- **Frontend Vitest Suite:** 41 passing tests across 6 test suites (0 failures in 4.5s).
- **TypeScript & Build:** `tsc -b && vite build` succeeds in 688ms with 0 errors.
- **Ruff Python Linter:** 82 minor lint issues identified (predominantly Python 3.12+ `datetime.UTC` aliases and formatting).
- **Mypy Static Typing:** 106 type issues identified across checked core modules (mostly implicit optional and SQLAlchemy column typing).
- **Oxlint Frontend Linter:** 30 warnings, 0 errors.

---

## 9. Offline Egress Test Plan

To scientifically verify the **"100% Offline / Zero Egress by Default"** guarantee:
1. **Network Egress Isolation Test:** Execute FastAPI backend and React frontend with loopback network namespace or offline dummy gateway (`127.0.0.1`).
2. **DNS & Socket Sniffing:** Monitor socket requests via `psutil` / network sniffer to ensure no outgoing connections occur to external IP addresses.
3. **Telemetry Opt-Out:** Verify ChromaDB telemetry is disabled (`ANONYMIZED_TELEMETRY=False`), OpenTelemetry is local-only, and Google Fonts are bundled locally in `frontend/public/fonts/`.
