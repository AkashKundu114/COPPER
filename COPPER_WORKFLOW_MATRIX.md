# Workflow Verification Matrix: Project A — C.O.P.P.E.R.

**Target Repository:** `D:\C.O.P.P.E.R`  
**Date:** October 16, 2026  
**Auditor:** QA & Integration Verification Team

---

## 1. Complete Workflow Inventory & Verification Status

| Workflow ID | Workflow Name | Entry Point / Route | Primary Components | Verification Type | Status | Evidence / Notes |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **WF-COP-01** | Application Boot & DB Init | `scripts/start_copper.bat` | `main.py:lifespan`, `db.py:init_db` | Real Execution | ✅ **PASS** | SQLite WAL mode verified; connection pool initializes cleanly; APScheduler starts background jobs. |
| **WF-COP-02** | Local Backend Port Discovery | `launch-desktop.js`, `electron-main.cjs` | `net.Socket`, `isPortOpen` | Real Execution | ✅ **PASS** | Checks port 8000; spawns uvicorn if inactive; handles existing instances without crashing. |
| **WF-COP-03** | Electron Window & QuickBar | Global `Alt+Space` | `createWindow()`, `createQuickBar()` | Real Execution | ✅ **PASS** | Window launches at 1360x860; transparent QuickBar mounts at top; blur hides QuickBar. |
| **WF-COP-04** | Electron Secure IPC Bridge | `preload.cjs` -> `electron-main.cjs` | `contextBridge`, `ipcMain.handle` | Real Execution | ✅ **PASS** | Whitelist enforced. Missing handlers (`get-activation-status`, `activate-local-gpu`, etc.) registered and tested. |
| **WF-COP-05** | Chat Messaging & Streaming | `POST /api/chat`, WS `/ws/chat` | `ChatDock.tsx`, `useBrainSocket.ts` | Unit + Mock E2E | 🟡 **MIXED** | Vitest verifies message dispatch, Enter key, and modes. Playwright mocks WS replies; real LLM stream requires local Ollama model. |
| **WF-COP-06** | Agent Dynamic Routing | `POST /api/route` | `TFP-Router`, `AgentRegistry.tsx` | Benchmark Run | ⚠️ **PARTIAL** | High accuracy on 1,390 curated cases (97.7%); drops to 56.87% on full 12,204 scaled dataset (`behavior`/`voice` 0% F1). |
| **WF-COP-07** | Guardian Safety Gate | `POST /api/guardian/evaluate` | `guardian.py:evaluate` | Regression Test | ✅ **PASS** | Destructive commands (rm -rf, format, python one-liners, piped shells) intercepted with `DisagreementLevel.SAFETY`. |
| **WF-COP-08** | Forge Sandbox Execution | `POST /api/sandbox/execute` | `ast_validator.py`, `kernel_sandbox.py` | Regression Test | ✅ **PASS** | AST gate blocks dynamic `getattr` dunder resolution and forbidden dunders (`__class__`, `__init__`, `__dict__`). |
| **WF-COP-09** | Epistemic Memory Revision | `POST /api/memory/revise` | `epistemic_revision.py`, `MemoryView.tsx` | Unit Test | ✅ **PASS** | Belief updates, surprise index calculation, and provenance chains verified. Tested on $N=6$ benchmark scenarios. |
| **WF-COP-10** | DAG Multi-Step Planning | `POST /api/planner/dag` | `nexus_planner.py`, `TaskGraph` | Unit Test | ✅ **PASS** | Parallel branch execution, cyclic dependency rejection, and upstream failure cascading tested and passing. |
| **WF-COP-11** | Smart Clipboard Intelligence | Background listener | `SmartClipboardDrawer.tsx` | Unit Test | ✅ **PASS** | Clipboard changes detected; cognitive load throttling suppresses alerts during active work sprints. |
| **WF-COP-12** | Voice & Wake-Word Service | `POST /api/voice/transcribe`, `/wake` | `openwakeword`, `kokoro-onnx` | Unit Test | 🟡 **MOCKED DEV** | Audio synthesis and transcription pipelines execute with valid WAV fixtures. Hardware mic capture requires audio device. |
| **WF-COP-13** | Document Search & Q&A | `POST /api/documents/search` | `DocumentReaderModal.tsx`, `pypdf` | Vitest + Pytest | ✅ **PASS** | Interactive tab switching, live search filtering, and text extraction verified across PDF, DOCX, and XLSX formats. |
| **WF-COP-14** | Autonomous Self-Improvement | `POST /api/self-improvement/evaluate` | `crucible_judge.py`, `SelfImprovementView` | Unit Test | ✅ **PASS** | Heuristic fallback and turn evaluation persist prompt patches without unhandled exceptions. |
| **WF-COP-15** | Accessibility Screen Reader | Live DOM live-regions | `ScreenReaderAnnouncer.tsx` | Vitest | ✅ **PASS** | `useAnnounce` triggers live region updates on navigation and agent reasoning state changes. |

---

## 2. Test Execution Breakdown

- **Total Backend Tests:** 625 unit/integration tests (`tests/`, `backend/tests/`)
- **Total Frontend Tests:** 41 component/a11y tests (`frontend/src/`)
- **Regressions Introduced:** 0
- **Blocked Workflows:** E2E live model generation blocked if local Ollama models are not downloaded.
