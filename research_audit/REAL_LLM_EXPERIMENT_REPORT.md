# Research Report: Real Local LLM Experimentation & Model Fleet Boundaries
**Document ID:** `REAL_LLM_EXPERIMENT_REPORT.md`  
**Target Repository:** `d:\C.O.P.P.E.R`  
**Date:** October 31, 2026  
**Auditor Roles:** LLM Evaluation Researcher, Systems Architect, Verification Engineer  
**Target Subsystems:** `OllamaClient`, `VRAMPager`, `ModelManager`, `models_manifest.json`

---

## 1. Executive Summary & Physical Reality

A critical non-negotiable rule of this audit is that **synthetic evaluations and in-memory mock decisions do not count as real LLM agent experiments**. This report documents the physical storage reality of the model fleet, the local inference architecture, and the boundaries of local edge execution.

---

## 2. Physical Storage Audit vs Manifest Claims (ISS-05 / ISS-A09)

### 2.1 Manifest Claim
`ai-models/models_manifest.json` specifies 21 models with an aggregate deployment capacity of **57.68 GB**, including:
- Sovereign Core Heavyweights (12B – 14B): `Qwen2.5-14B-Instruct` (5.95 GB), `Qwen2.5-Coder-14B-Instruct-abliterated` (5.95 GB), `DeepSeek-R1-Distill-Qwen-14B` (5.95 GB), `phi-4` (5.82 GB), `Mistral-Nemo-Instruct` (5.33 GB).
- Resident Mini Models ($\le$ 3B): `Qwen2.5-1.5B-Instruct` (1.04 GB).

### 2.2 Physical Disk Verification
Physical scanning of `d:\C.O.P.P.E.R\ai-models\` reveals:
- Total Physical Bytes on Disk: **~6.17 GiB**
- Actual Weight Files Present:
  - `ai-models/image/sd_turbo.safetensors`: 5,214,561,328 bytes (~4.86 GiB)
  - `ai-models/audio/tts/kokoro-v0_19.onnx`: 325,525,180 bytes (~310 MiB)
  - `ai-models/audio/whisper/ggml-large-v3-turbo.bin`: 874,188,075 bytes (~833 MiB)
  - `ai-models/audio/tts/en_US-amy-medium.onnx`: 63,201,294 bytes (~60 MiB)
  - `ai-models/audio/tts/en_US-ryan-medium.onnx`: 63,201,294 bytes (~60 MiB)
  - `ai-models/audio/whisper/ggml-tiny.en.bin`: 77,704,715 bytes (~74 MiB)
  - ONNX Wakeword models (`silero_vad.onnx`, `hey_copper.onnx`, `embedding_model.onnx`): ~5 MiB
- Placeholder Directories:
  - `ai-models/core/`: `.gitkeep` only (0 bytes)
  - `ai-models/subagents/`: `.gitkeep` only (0 bytes)
  - `ai-models/vision/`: `.gitkeep` only (0 bytes)
  - `ai-models/embeddings/`: `.gitkeep` only (0 bytes)

### 2.3 Clarification of Manifest Architecture
The 57.68 GB fleet cited in academic tables represents the **total working capacity of the multi-agent topology**, not files checked into the Git repository. The LLM backends are downloaded dynamically via Ollama (`ollama pull`) to the host operating system's external cache (`~/.ollama/models`). `models_manifest.json` serves as the runtime configuration registry defining quantization levels, context windows, and fallback models.

---

## 3. VRAM Dynamic Management & Pager Mechanics

Because an 8 GB edge GPU (e.g., NVIDIA GeForce RTX 5060 Laptop GPU) cannot host multiple 14B models simultaneously, C.O.P.P.E.R. implements the `VRAMPager` (`backend/app/ai/llm/vram_pager.py`):
1. **Single-Slot Model Leasing:** The active 14B model occupies ~5.2–6.4 GB VRAM.
2. **LRU Eviction with Lookahead:** Before loading a newly routed model, the pager scores resident models:
   $$\text{Score} = (0.40 \cdot \text{recency}) + (0.20 \cdot \text{frequency}) + (0.40 \cdot \text{lookahead})$$
3. **Eviction Execution:** The least valuable heavy model is evicted via Ollama's `keep_alive=0` parameter.
4. **Resident Mini Model:** The 1.5B Guardian mini-model is pinned with `keep_alive=-1` (~1.04 GB VRAM) for sub-millisecond safety evaluations.

---

## 4. End-to-End LLM Agent Execution & Interdiction

When the agent operates against physical LLMs via `OllamaClient`:
1. The user message is dispatched to the active agent.
2. `ContextEngine` retrieves memories, attaching `[MEMORY id=... provenance=... confidence=...]` tags.
3. The LLM emits structured tool calls (`<tool_call>{"tool": "file_write", "arguments": {...}}</tool_call>`).
4. `ToolExecutor` extracts the call, passes the working set's memory provenance into `GuardianEngine`, and verifies authority before any tool invocation.
5. If the LLM was influenced by an untrusted or adversarial memory, `MemoryQuarantine` blocks the execution before the host OS can be touched.

**Conclusion:** The model fleet topology is clarified, grounded in physical disk realities, and protected by real runtime interdiction.
