# COPPER Framework — Technical Requirements Document (TRD)

> **Documentation set:** [PRD](PRD.md) · [TRD](TRD.md) · [App Flow](APP_FLOW.md) · [UI/UX Brief](UI_UX_BRIEF.md) · [Backend Schema](BACKEND_SCHEMA.md) · [Implementation Guide](IMPLEMENTATION.md)

---

## 6. System Architecture Overview

### 6.1 Architecture Pattern: Sequential Hot-Swap Engine

COPPER does **not** use a parallel multi-agent architecture. Instead, it implements a **State-Persistent Sequential Execution** pattern.

> **Core Invariant:** Only one model may occupy VRAM at any given nanosecond. All context is persisted in `state.json` (volatile relay) and `copper.db` (persistent memory) so models can be fully unloaded without data loss.

### 6.2 The 6-Model Specialist Architecture

| Model Profile | Base Model | Target Agents | VRAM | Quant |
|---|---|---|---|---|
| **Model 1: Core Reasoning** | DeepSeek-R1-Distill-Qwen-14B or Qwen2.5-14B | COPPER, CHRONOS | 5.2 GB | Q4_K_M |
| **Model 2: Code Engineering** | Qwen2.5-Coder-7B-Instruct | CYPHER, CRUCIBLE, FORGE, NEXUS, ARGUS | 4.8 GB | Q4_K_M |
| **Model 3: OS Executors** | Llama-3.2-3B or Qwen2.5-3B | AXIS, ATLAS, KINETIC, PULSE, ZENITH, LEDGER | 2.2 GB | Q4_K_M |
| **Model 4: Vision & RPA** | Florence-2-large or Qwen2-VL-7B | HAWK, TALON, PORTAL, IRIS | 0.8–4.5 GB | FP16/INT4 |
| **Model 5: Web & Streaming** | Qwen2.5-7B-Instruct | RAPTOR, PHANTOM, VANGUARD, AETHER, BEACON, GLITCH, DIRECTOR | 4.5 GB | Q4_K_M |
| **Model 6: Audio / Speech** | Faster-Whisper-tiny + Kokoro-82M | SONAR, ORACLE, HERMES, AEON | 0 GB | CPU/ONNX |

### 6.3 Memory Allocation Strategy

**GGUF CPU Layer Offloading:** For the 14B reasoning model, GGUF layer offloading via `llama.cpp` allows partial execution:

- Total layers (14B model): approximately 40
- VRAM-resident layers: 28 (filling ≈ 5.2 GB)
- System RAM-offloaded layers: 12 (consuming ≈ 2.5 GB RAM)
- **Effect:** Slower token generation, but guaranteed OOM safety

### 6.4 Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Inference Engine | Ollama + llama.cpp | Model loading, GGUF quantization, VRAM management |
| Orchestration | Python 3.11+ | Sequential pipeline, state management, daemon processes |
| Active State | `state.json` (local SSD) | Live relay baton between agents |
| Long-Term Memory | SQLite (`copper.db`) | Chat history, agent logs, episodic memory, temporal tasks |
| Vector Retrieval | ChromaDB (local) | RAG over personal documents (ECHO agent) |
| Vision Models | Hugging Face Transformers | Florence-2 for screen grounding |
| Audio I/O | Faster-Whisper + Kokoro | STT + TTS pipeline on CPU |
| Fine-Tuning | Unsloth + QLoRA + TRL | Personality adapter training |
| Frontend Dashboard | React + Tailwind CSS | Live telemetry UI, glassmorphism aesthetic |
| RPA | pyautogui + OpenCV | Mouse/keyboard automation, screen diffing |
| Browser Automation | Playwright | Headless browser for PHANTOM agent |
| Clipboard | pyperclip | Shared clipboard context injection |
| Window Detection | pygetwindow / Xlib | Active workspace context awareness |
| Scheduler | APScheduler + `clock_daemon.py` | Alarms, reminders, polling triggers |

---

## 7. Technical Requirements

### 7.1 TR-01: Model Lifecycle Management

- All Ollama inference calls **MUST** include `"keep_alive": 0` to enforce immediate VRAM release post-inference
- Python garbage collection **MUST** be invoked after every model session: `gc.collect(); torch.cuda.empty_cache()`
- No two models may be loaded into VRAM simultaneously under any code path

### 7.2 TR-02: Context Window Enforcement

- Maximum context window for 7B and 14B models: **4,096 tokens**
- Context window caps must be enforced in Ollama model configuration files
- State summaries passed between agents must be pre-compressed to stay under **2,048 tokens**

### 7.3 TR-03: Sequential Execution

- The main orchestration loop **MUST** use sequential `for` loops, never `asyncio.gather` or `threading.Thread`
- Parallel execution of any AI inference task is a critical failure

### 7.4 TR-04: State File Integrity

- `state.json` must be written **atomically** (write to temp file, then rename) to prevent corruption
- All agents must validate `state.json` structure on read; malformed state must trigger COPPER error-recovery path
- `state.json` must not exceed **1 MB**; execution logs must be rotated to SQLite after **100 entries**

### 7.5 TR-05: LoRA Adapter Hot-Swap

- Each personality adapter must be a standalone GGUF/LoRA file under **40 MB**
- Adapter injection must occur in **under 100 milliseconds**
- Adapter files must be stored at `./adapters/<agent_id>_adapter/`

### 7.6 TR-06: Security Guardrails (AXIS / TALON)

- **Command Whitelist Enforcement:** Block all shell commands containing `rm -rf`, `format`, `del /f`, `dd if`, `mkfs` at the Python framework level before reaching the terminal
- **Visual Confirmation Mode:** Any file-destructive or GUI-click action must pause, display a confirmation prompt, and require explicit `Y` approval from the user
- TALON must operate within a coordinate sandbox bounding box configured to the active display resolution

### 7.7 TR-07: Background Daemon Requirements

| Daemon | Polling Interval | RAM Footprint Limit |
|---|---|---|
| `clock_daemon.py` | Every 60 seconds (SQLite `temporal_tasks`) | ≤ 15 MB |
| `kinetic_daemon.py` | Weather: every 30 min · Twitch/YT live: configurable (default 5 min) | ≤ 20 MB |
| `screen_diff.py` | Every 5 seconds when active (OpenCV pixel diff) | ≤ 40 MB |
| Wake-word listener (Porcupine/Rustpotter) | CPU-pinned, always-on | ≤ 20 MB |
