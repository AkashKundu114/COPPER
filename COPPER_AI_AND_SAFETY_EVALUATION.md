# AI, LLM, Memory, Voice & Safety Evaluation: Project A — C.O.P.P.E.R.

**Target Repository:** `D:\C.O.P.P.E.R`  
**Date:** October 16, 2026  
**Auditor:** Senior AI Systems Architect & Red-Team Reviewer  

---

## 1. Local LLM & Inference Engine

### 1.1 Model Discovery & Execution Architecture
- **Inference Router:** [backend/app/ai/llm/engine.py](file:///D:/C.O.P.P.E.R/backend/app/ai/llm/engine.py)
- **Supported Backends:** Local Ollama HTTP daemon (`http://127.0.0.1:11434`) and fallback local GGUF llama.cpp subprocess.
- **Hardware Detection:** NVIDIA CUDA GPU detection checks compute capability via `torch.cuda` or NVML subprocess. Falls back cleanly to multi-threaded CPU execution.
- **VRAM Discipline:**
  - Active VRAM telemetry monitored via `systemAPI.getTelemetry()` every 4000ms.
  - Context length capped at 8,192 tokens per turn; streaming chunks yield tokens via async generators to minimize memory buffering.
- **Model Inventory Reality Check:**
  - `ai-models/core/`, `ai-models/subagents/`, and `ai-models/embeddings/` directories contain only empty `.gitkeep` files.
  - The claimed 47 GB sovereign model weights are not pre-bundled on disk. In a fresh installation, the user must pull models via `ollama pull llama3.2:3b`.
  - The application handles this gracefully by detecting missing model errors and rendering setup guidance.

---

## 2. Epistemic Memory & Belief Revision System

- **Core Module:** [backend/app/ai/memory/epistemic_revision.py](file:///D:/C.O.P.P.E.R/backend/app/ai/memory/epistemic_revision.py)
- **Mechanism:**
  - Probabilistic Weighted Epistemic Belief Revision (PW-EBR).
  - Maintains belief graphs with node surprise metrics $S(e) = -\log_2 P(e \mid B)$ and contradiction resolution cascades.
  - Stores memory nodes in SQLite `copper_memory.db` with WAL mode enabled.
- **Evaluation Claims vs. Reality:**
  - The README advertises "100% Robustness vs 33% Naive Bayes".
  - Empirical verification revealed that the evaluation script (`backend/eval/benchmark_belief_revision.py`) tests only **$N = 6$ hand-crafted scenarios**.
  - The "Naive Bayes" baseline in the script is implemented as simple linear addition/subtraction (`conf = conf + 0.10` / `conf - 0.10`), which is a simplified strawman rather than Bayesian log-odds updating.
  - **Verdict:** The epistemic revision logic functions as an effective rule-based belief updater, but the comparative benchmark is illustrative rather than statistical proof.

---

## 3. Voice, Audio & Wake-Word Pipeline

- **Components:**
  - Wake-Word Engine: `openwakeword` with models for "Hey Copper".
  - Voice Activity Detection: `webrtcvad` frame energy gating.
  - Text-to-Speech: `kokoro-onnx` neural speech synthesizer and fallback `pyttsx3`.
- **Failure Recovery:**
  - When no microphone is connected or audio devices are occupied, the pipeline emits a non-fatal warning and operates in text-only mode.
  - Automated unit tests in `tests/audio/test_audio_pipeline.py` verify WAV header structure, silence detection, and playback resource cleanup.

---

## 4. Benchmark Analysis: Curated vs. Scaled Routing

### 4.1 Routing Precision Discrepancy
- **README Claim:** 97.77% routing precision, 98.78% weighted F1 across 1,390 cases.
- **Full Empirical Test Run:** Found in `backend/eval/benchmark_metrics.json` across 12,204 samples:
  - Total Samples: 12,204 | Correct: 6,940
  - Overall Accuracy: **56.87%**
  - Weighted F1 Score: **57.10%**
  - Category `behavior`: 0.0% F1 (1,148 misrouted samples)
  - Category `voice`: 0.0% F1 (1,224 misrouted samples)
  - Category `chat`: Acts as an oversized fallback bucket (20.01% precision)
- **Root Cause:** Keyword-based routing rules in `KEYWORD_RULES` lack distinct semantic patterns for behavioral optimization and voice commands, causing them to fall through to the default chat agent.

### 4.2 Remediation Guidance
1. Update README documentation to clarify that 97.77% represents the curated core test partition ($n=1,390$).
2. Expand routing keywords and semantic vector centroids for `behavior` and `voice` domains.
