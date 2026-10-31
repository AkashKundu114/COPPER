# C.O.P.P.E.R. Architecture & System Topology

**Centralized Omnifunctional Personal Productivity and Execution Routine**  
*Comprehensive Technical Architecture, Process Boundaries, Data Flows, and Lifecycle Specification*

---

## 1. System Topology Overview

C.O.P.P.E.R. is an independent, 100% offline, local-first personal AI agent runtime environment (executing in user-space). The platform couples a React 19 desktop interface running inside Electron 44 with a high-throughput asynchronous FastAPI backend running on local Python 3.11+. Local intelligence is powered by quantized language models via Ollama, local embeddings in ChromaDB, and an epistemic memory graph backed by SQLite in Write-Ahead Logging (WAL) mode.

```mermaid
graph TD
    subgraph Desktop Shell ["Desktop Shell (Electron 44)"]
        UI["React 19 Frontend<br/>(Tailwind v4, Framer Motion)"]
        Preload["Secure Preload Script<br/>(Context Isolation, 12 IPC Channels)"]
        Main["Electron Main Process<br/>(Window Lifecycle, Process Guardian)"]
        UI <-->|DOM Events / IPC| Preload
        Preload <-->|Filtered IPC| Main
    end

    subgraph Backend Core ["Backend Services (FastAPI 0.141)"]
        Router["TFP-Router<br/>(Regex + Dynamic Cache)"]
        Guardian["DFM-Guard Safety Firewall<br/>(Levels 0-3 Friction)"]
        Agents["12 Production Specialized Agents"]
        Sandbox["Forge Code Sandbox<br/>(AST Gate + Subprocess Limits)"]
        Voice["Multimodal Voice Pipeline<br/>(openWakeWord + Whisper + Piper)"]
        Memory["Epistemic Decaying Memory<br/>(Bayesian Revision + Decay)"]
    end

    subgraph Sovereign Storage ["Local Sovereign Storage"]
        Chroma["ChromaDB Vector Store<br/>(Embedding Collections)"]
        SQLite["SQLite / WAL Mode<br/>(Fact Graph, Sessions, Audits)"]
        Ollama["Local Ollama Instance<br/>(127.0.0.1:11434 GGUF Fleet)"]
    end

    Main -->|Spawn / Monitor Port 8000| Backend Core
    UI <-->|REST HTTP & WebSocket ws://127.0.0.1:8000| Router
    Router --> Guardian
    Guardian --> Agents
    Agents --> Sandbox
    Agents --> Voice
    Agents --> Memory
    Memory <--> Chroma
    Memory <--> SQLite
    Agents <--> Ollama
```

---

## 2. Process Boundaries & Execution Lifecycle

### 2.1 Startup & Initialization Sequence
1. **Electron Shell Initialization:**
   - [`frontend/electron-main.cjs`](file:///D:/C.O.P.P.E.R/frontend/electron-main.cjs) initializes Chromium with `--force_high_performance_gpu` and `--force-renderer-accessibility`.
   - Single-instance lock (`app.requestSingleInstanceLock()`) guarantees only one master instance runs.
   - Electron probes TCP port 8000 (`isPortOpen(8000)`). If port 8000 is inactive, it spawns Python Uvicorn in the background:
     `python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`.
   - Window creation: Main HUD Window (`1360x860`, minimum `1024x700`) and the ambient QuickBar overlay (`680x72`, toggled via `Alt+Space`).

2. **FastAPI Lifespan Bootstrapping:**
   - [`backend/app/main.py:lifespan`](file:///D:/C.O.P.P.E.R/backend/app/main.py#L90-L113) executes:
     1. Database initialization (`init_db()`): Configures SQLite tables with `PRAGMA journal_mode=WAL;` and `PRAGMA synchronous=NORMAL;`.
     2. Loads active prompt patches from disk (`load_applied_patches_from_db()`).
     3. Initializes OpenTelemetry only if explicitly enabled (`OTEL_ENABLED=True`); otherwise stays 100% airgapped.
     4. Starts `AsyncIOScheduler` for ambient background jobs (memory compaction, clipboard monitoring, daily debriefs).
     5. Starts `model_tier_manager` to monitor GPU VRAM allocation.
     6. Starts `clipboard_monitor` for passive context tracking.

3. **Graceful Shutdown & Teardown:**
   - Electron signals `before-quit`, unregisters all global shortcuts, and issues a graceful shutdown to the background Uvicorn process.
   - FastAPI lifespan shutdown safely isolates individual component teardowns:
     1. `wake_word_service.disable()` stops audio streams and releases PortAudio handles.
     2. `clipboard_monitor.stop()` halts clipboard polling.
     3. `model_tier_manager.stop()` evicts active worker pools.
     4. `stop_scheduler()` terminates background jobs without dropping in-flight writes.
     5. `diffusion_engine.unload()` frees any cached PyTorch diffusion tensors.
     6. `close_chroma_client()` flushes vector embeddings to disk.
     7. `close_db()` closes active SQLite connection pools.

---

## 3. The 12-Agent Production Topology

COPPER enforces a strict contract between frontend and backend agent definitions:

| Agent Identifier | Codename | Specialized Domain | Model Architecture | Primary Tools & Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| `chat` | General Conversationalist | Default fallback & open dialogue | Qwen2.5-14B / 8B | Contextual dialogue, general Q&A |
| `coding` | AXIS Code Specialist | Code synthesis, refactoring, tests | Qwen2.5-Coder-14B | AST analysis, forge sandbox, linter |
| `document` | Document Synthesizer | Document drafting, analysis, summaries | Mistral-Nemo-12B | PDF/Word parsing, markdown exports |
| `automation` | System Automator | Shell tasks, file manipulation, workflows | SmolLM2-1.7B | Kernel sandbox, filesystem tools |
| `reminder` | Temporal Assistant | Time tracking, deadlines, calendar | Qwen2.5-1.5B | Cron scheduler, system notifications |
| `research` | Deep Researcher | Academic papers, scientific queries | DeepSeek-R1-Distill-14B | Hybrid search, citation formatter |
| `vision` | Visual Interpreter | Image analysis, OCR, visual reasoning | Qwen2.5-VL-3B | Multimodal OCR, screen inspection |
| `image` | Creative Diffusion Studio | Image synthesis & editing | SD-Turbo (1-step) | Local latent diffusion, asset export |
| `web_search` | Grounded Searcher | Real-time web retrieval | SmolLM2-1.7B | SearXNG local API, link extraction |
| `campaign_intelligence` | Ad-Tech Optimizer | Ad analytics & budget optimization | Mistral-Nemo-12B | Z-score anomaly detection, log-curve budgeter |
| `planner` | Nexus Planner | Complex task decomposition, DAGs | Qwen2.5-14B | DAG cascade executor, topological scheduler |
| `guardian` | DFM-Guard Alignment | Safety, boundary, and friction | Qwen2.5-1.5B | Red-team filtering, AST validation, friction modals |

> [!NOTE]
> `voice` and `behavior` are explicitly tracked under `PLANNED_AGENTS` in [`frontend/src/constants/agents.ts`](file:///D:/C.O.P.P.E.R/frontend/src/constants/agents.ts). Handlers for these will be activated in upcoming milestones. Parity is verified by [`tests/ai/test_agent_consistency.py`](file:///D:/C.O.P.P.E.R/tests/ai/test_agent_consistency.py).

---

## 4. Subsystem Architectures

### 4.1 TFP-Router (Topological Failure-Predicting Cascade Router)
- **File:** [`backend/app/ai/orchestration/router.py`](file:///D:/C.O.P.P.E.R/backend/app/ai/orchestration/router.py)
- **Stage 0 (Exact Cache):** Hash-based dynamic cache lookup (< 0.05ms).
- **Stage 1 (Pre-compiled Keyword/Regex Rules):** 12 compiled pattern blocks evaluating intent patterns (< 0.10ms).
- **Stage 2 (Semantic Vector Retrieval):** Cosine similarity against dynamic routing centroids in ChromaDB (< 2.5ms).
- **Stage 3 (DAG Cascade Risk Prediction):** Evaluates multi-step dependency failure probability ($\mathcal{R}_{\text{cascade}}$).

### 4.2 DFM-Guard Safety Firewall
- **File:** [`backend/app/core/guardian.py`](file:///D:/C.O.P.P.E.R/backend/app/core/guardian.py)
- **Disagreement Levels:**
  - **Level 0 (EXECUTE):** Benign operations, read-only queries, general conversation.
  - **Level 1 (NUDGE):** Minor ambiguities or optimization recommendations.
  - **Level 2 (CHALLENGE):** Reversible file modifications, external network requests, elevated tool calls. Triggers confirmation prompt.
  - **Level 3 (SAFETY BOUNDARY):** Irreversible disk operations (`rm -rf /`, `format c:`), credential exfiltration, obfuscated shell evasion (Base64/Hex decoders, LOLBAS). Hard refusal with structured security explanation.

### 4.3 Epistemic Decaying Memory
- **Files:** [`backend/app/ai/memory/epistemic_memory.py`](file:///D:/C.O.P.P.E.R/backend/app/ai/memory/epistemic_memory.py), [`backend/app/ai/memory/hybrid_retriever.py`](file:///D:/C.O.P.P.E.R/backend/app/ai/memory/hybrid_retriever.py)
- **Confidence Tiers:**
  - Fact: $C \ge 0.85$
  - Observation: $0.50 \le C < 0.85$
  - Hypothesis: $0.10 \le C < 0.50$
- **Decay Formula:**
  $$C_i(\Delta t) = \max\left(C_{\text{floor}}(m_i),\, C_{i, 0} \cdot e^{-\lambda_{\text{eff}}(m_i) \cdot \Delta t}\right)$$
- **Hybrid Retrieval:** Reciprocal Rank Fusion (RRF) combining BM25 keyword matching with dense embeddings from ChromaDB.

### 4.4 Forge Code Execution Sandbox
- **Files:** [`backend/app/core/ast_validator.py`](file:///D:/C.O.P.P.E.R/backend/app/core/ast_validator.py), [`backend/app/core/kernel_sandbox.py`](file:///D:/C.O.P.P.E.R/backend/app/core/kernel_sandbox.py)
- **Layer 1 (AST Validator):** Inspects syntax trees before execution. Forbids `os`, `sys`, `subprocess`, `ctypes`, `socket`, dangerous builtins (`eval`, `exec`), and dynamic dunder reflections (`__subclasses__`, `__globals__`).
- **Layer 2 (Kernel Sandbox):** Executes verified scripts with `stdin=DEVNULL`, hard memory caps (256 MB), and strict execution timeouts (15 seconds).
