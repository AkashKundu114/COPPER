# Research Note: Model Selection Rationale

> **Documentation hub:** [docs/README.md](../README.md) · **Research index:** [research/README.md](README.md) · **Related:** [TRD §6.2](../TRD.md#62-the-6-model-specialist-architecture)
>
> **Status:** Draft

---

## Purpose

[TRD §6.2](../TRD.md#62-the-6-model-specialist-architecture) defines six model profiles. This note records the reasoning behind each choice so future model swaps (e.g. when a smaller/better quantization becomes available) can be evaluated against the original constraints rather than guessed at.

---

## Constraint Recap

Every model choice is bounded by two numbers from [PRD §5](../PRD.md#5-hardware-constraints--performance-targets):

- **Peak VRAM ≤ 5.5 GB** — applies to whichever single model is currently loaded (Model 1–5; Model 6 is CPU-only)
- **Context window ≤ 4,096 tokens** — applies uniformly across Model 1–5

---

## Profile-by-Profile Notes

### Model 1 — Core Reasoning (COPPER, CHRONOS)

- **Candidates:** DeepSeek-R1-Distill-Qwen-14B, Qwen2.5-14B (both Q4_K_M)
- **Why 14B:** COPPER's routing decisions and CHRONOS's task decomposition are the highest-stakes reasoning steps in the loop — a weaker model here produces bad `next_agent`/`next_model` routing that cascades through the entire cycle.
- **VRAM tradeoff:** At 5.2 GB, this profile consumes nearly the entire 5.5 GB ceiling, which is why [TRD §6.3](../TRD.md#63-memory-allocation-strategy) specifies GGUF layer offloading (28 of ~40 layers in VRAM, 12 offloaded to system RAM).
- **Open question:** DeepSeek-R1-Distill's reasoning-trace style may produce verbose `<think>` blocks that eat into the 4,096-token context cap — needs validation against [TRD §7.2](../TRD.md#72-tr-02-context-window-enforcement)'s 2,048-token inter-agent compression budget.

### Model 2 — Code Engineering (CYPHER, CRUCIBLE, FORGE, NEXUS, ARGUS)

- **Choice:** Qwen2.5-Coder-7B-Instruct, Q4_K_M, 4.8 GB
- **Why:** This profile serves five agents covering the full code lifecycle (write, debug, design, version-control, review). A coder-tuned model is non-negotiable here; 7B at Q4_K_M is the largest coder model that comfortably fits under 5.5 GB alongside its KV cache at 4,096 tokens.
- This is also the **fine-tuning target** in [Implementation Guide §15](../IMPLEMENTATION.md#15-fine-tuning-pipeline) — LoRA adapters for all five agents in this group share the same base model.

### Model 3 — OS Executors (AXIS, ATLAS, KINETIC, PULSE, ZENITH, LEDGER)

- **Candidates:** Llama-3.2-3B, Qwen2.5-3B, Q4_K_M, 2.2 GB
- **Why small:** These six agents perform comparatively mechanical tasks (shell commands, file ops, scheduling, monitoring, spreadsheet manipulation) that don't require frontier reasoning. The low VRAM footprint (2.2 GB) leaves headroom for this profile to be loaded *alongside* a brief Model 4 vision check without exceeding 5.5 GB — though [TRD §7.1](../TRD.md#71-tr-01-model-lifecycle-management) still prohibits this in practice (single active model policy).

### Model 4 — Vision & RPA (HAWK, TALON, PORTAL, IRIS)

- **Candidates:** Florence-2-large or Qwen2-VL-7B, 0.8–4.5 GB, FP16/INT4
- **Why the range:** Florence-2-large (0.8 GB) is far cheaper than Qwen2-VL-7B (up to 4.5 GB) but isn't natively served by Ollama — see [Implementation Guide §18](../IMPLEMENTATION.md#18-known-limitations--mitigations) and the open question below.
- **Tradeoff:** Florence-2 is preferred for the *default* path (cheap, fast bounding-box detection for HAWK/TALON) with Qwen2-VL-7B as a fallback for more complex OCR/scene-understanding tasks (IRIS).

### Model 5 — Web & Streaming (RAPTOR, PHANTOM, VANGUARD, AETHER, BEACON, GLITCH, DIRECTOR)

- **Choice:** Qwen2.5-7B-Instruct, Q4_K_M, 4.5 GB
- **Why:** This profile handles the largest agent group (7 agents) but the tasks are largely "read a page / API response and summarize or extract structured data" — a strong general-purpose 7B instruct model is sufficient without needing coder- or vision-specific tuning.

### Model 6 — Audio / Speech (SONAR, ORACLE, HERMES, AEON)

- **Choice:** Faster-Whisper-tiny (STT) + Kokoro-82M (TTS), CPU/ONNX, 0 GB VRAM
- **Why CPU-only:** Audio I/O agents (including HERMES/AEON, which are mail/calendar coordinators bundled into this profile for VRAM-budget reasons rather than functional similarity) run continuously or near-continuously for proactive features. Keeping them off the GPU entirely means they never compete with Model 1–5 for the 5.5 GB budget — this is what allows [PRD US-05](../PRD.md#us-05-local-media-transcription)'s "Total operation uses 0 GB VRAM" acceptance criterion.
- **Tradeoff:** Whisper-tiny trades accuracy for footprint — flagged in [Implementation Guide §18](../IMPLEMENTATION.md#18-known-limitations--mitigations) as an acceptable v1.0 limitation with an upgrade path to `small`/`base`.

---

## Open Question: Florence-2 / Ollama Integration

Florence-2 is not currently servable through Ollama's standard model registry. [Implementation Guide §18](../IMPLEMENTATION.md#18-known-limitations--mitigations) proposes running it as a separate Hugging Face Transformers subprocess alongside the Ollama-served profiles. This has two implications worth tracking:

1. **VRAM accounting:** A separate Python/Transformers process loading Florence-2 needs its own `flush_vram()`-equivalent cleanup, distinct from the Ollama `keep_alive: 0` mechanism used for Model 1–3/5.
2. **Sequential guarantee:** [TRD §7.3 TR-03](../TRD.md#73-tr-03-sequential-execution) requires that no two models occupy VRAM simultaneously — the orchestration loop must explicitly serialize "Ollama model unloaded" → "Florence-2 subprocess loaded" rather than assuming Ollama's `keep_alive` flush is sufficient on its own.

Until resolved, treat Model 4's effective VRAM ceiling as the Qwen2-VL-7B figure (4.5 GB) for safety margin calculations, not the Florence-2 figure (0.8 GB).
