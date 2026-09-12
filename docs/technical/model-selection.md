# Model Selection & Orchestration Topology (v3.0)

## 1. Local Model Architecture Strategy

**C.O.P.P.E.R.** is engineered for ultra-low latency, 100% offline inference on modern consumer hardware (AMD Ryzen 9 / NVIDIA RTX 5060 Laptop GPU with 8GB VRAM).

To achieve maximum cognitive capability without exceeding the 8GB VRAM constraint, C.O.P.P.E.R. implements a **Tiered Model Hierarchy** featuring:
- **5 Heavyweight 12B–14B Cognitive Specialists** (transiently loaded on demand in a single active GPU slot ~5.2–6.4 GB).
- **6 Resident Mini Models (<=3B)** providing zero-latency firewall, reflex routing, code linting, shell safety, micro-reasoning, memory extraction, and desktop OCR.
- **C.O.P.P.E.R Sovereign Meta-Agent** continuously fine-tuning via QLoRA from daily interaction telemetry, tools, and user preferences.

---

## 2. Master Model Fleet Architecture

```
                                  ┌────────────────────────┐
                                  │  Ambient Mic / Speech  │
                                  └───────────┬────────────┘
                                              │ (Silero VAD v5 + openWakeWord)
                                  ┌───────────▼────────────┐
                                  │ "Hey COPPER" Detection │
                                  └───────────┬────────────┘
                                              │
                                  ┌───────────▼────────────┐
                                  │ Whisper Large v3 Turbo │
                                  └───────────┬────────────┘
                                              │
                                  ┌───────────▼────────────┐
                                  │   AEGIS / MERCURY      │
                                  │   (Qwen2.5 1.5B)       │ <--- Always-on (keep_alive: -1, ~940 MB VRAM)
                                  └───────────┬────────────┘
         ┌──────────────────┬─────────────────┼─────────────────┬──────────────────┐
         │                  │                 │                 │                  │
┌────────▼────────┐ ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐ ┌────────▼────────┐
│  ATLAS / COPPER │ │ VULCAN        │ │ PROMETHEUS    │ │ SCRIBE        │ │ DAEMON          │
│  Qwen2.5 14B    │ │ Qwen2.5-Coder │ │ DeepSeek-R1   │ │ Phi-4 14B     │ │ Mistral-Nemo    │
│  (Chat/Meta)    │ │ 14B Abliterated│ │ 14B Distill   │ │ (Documenter)  │ │ 12B (Tool Ops)  │
└────────┬────────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └────────┬────────┘
         │                  │                 │                 │                  │
         └──────────────────┴────────┬────────┴─────────────────┴──────────────────┘
                                     │
       ┌─────────────────────────────┼─────────────────────────────┐
       │                             │                             │
┌──────▼───────┐             ┌───────▼───────┐             ┌───────▼───────┐
│ ARGUS Vision │             │ PICASSO       │             │ Fast Reflex   │
│ Qwen2.5-VL   │             │ SD-Turbo      │             │ Mini Fleet    │
│ 3B Q4_K_M    │             │ Safetensors   │             │ 6 Quantized   │
└──────────────┘             └───────────────┘             └───────────────┘
```

---

## 3. Tier Breakdown

### Tier 1: Primary Core Heavyweights (12B – 14B Cognitive Tier)

*Loaded on-demand into GPU VRAM (1 active model slot at a time); managed by `ModelTierManager` with automatic idle eviction after 60s–120s.*

| Agent Codename | Role | Base Model | Quantization | Size | Purpose & Specialization |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **ATLAS** | Primary Orchestrator & Conversationalist | `Qwen2.5-14B-Instruct` | IQ3_XS | 5.95 GB | Multi-turn dialogue, high-level task decomposition, emotional resonance. |
| **VULCAN** | Software Architect | `Qwen2.5-Coder-14B-Instruct-abliterated` | IQ3_XS | 6.38 GB | Full-stack software engineering, reverse engineering, sandbox code execution. |
| **PROMETHEUS** | Cognitive Reasoner & Scientist | `DeepSeek-R1-Distill-Qwen-14B` | IQ3_XS | 6.38 GB | Deep chain-of-thought math proofs, logic verification, scientific research. |
| **SCRIBE** | Academic Synthesis & Documenter | `phi-4` | IQ3_XS | 6.24 GB | Authoritative reports, multi-format documents (PDF, Word, LaTeX, Excel). |
| **DAEMON** | System Automator & Tool Chainer | `Mistral-Nemo-Instruct-2407` | IQ3_M | 5.72 GB | Deterministic tool calling, OS shell control, API integration. |
| **C.O.P.P.E.R.** | Sovereign Meta-Agent | `Qwen2.5-14B-Instruct` + QLoRA | IQ3_XS | 5.95 GB | Continuously trained on user interaction telemetry with distinct personality & dry wit. |

---

### Tier 2: Resident Reflex Mini Fleet (<=3B)

*Optimized for sub-millisecond reflexes and resident memory footprints.*

| Agent Codename | Role | Base Model | Quantization | Size | Responsibility |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **AEGIS** | Sentinel Firewall | `Qwen2.5-1.5B-Instruct` | Q4_K_M | 0.94 GB | Zero-latency PII redaction, secret mask, prompt injection defense. |
| **MERCURY** | Reflex Router | `Qwen2.5-1.5B-Instruct` | Q4_K_M | 0.94 GB | Sub-30ms user intent classification and agent dispatch. |
| **BABEL** | Multilingual Normalizer | `Qwen2.5-1.5B-Instruct` | Q4_K_M | 0.94 GB | Multilingual translation to concise technical English. |
| **FORGE** | Code Linter & Git Author | `Qwen2.5-Coder-3B-Instruct` | Q4_K_M | 1.80 GB | Real-time AST syntax linting and Conventional Commit messages. |
| **WARDEN** | Shell Safety Gatekeeper | `Qwen2.5-Coder-3B-Instruct` | Q4_K_M | 1.80 GB | Pre-flight audit of terminal commands and Docker flags. |
| **CRUCIBLE** | Diagnostics & Self-Healing | `DeepSeek-R1-Distill-Qwen-1.5B` | Q4_K_M | 1.04 GB | Micro-reasoner for stack trace analysis and step checklists. |
| **CHRONOS** | Memory Consolidator | `SmolLM2-1.7B-Instruct` | Q4_K_M | 1.00 GB | User fact, preference, and relationship extraction for ChromaDB. |
| **SPIDER** | DOM & Web Cleaner | `SmolLM2-1.7B-Instruct` | Q4_K_M | 1.00 GB | Raw HTML scraping and clean markdown fact extraction. |
| **ORACLE** | SQL & Schema Guard | `granite-3.2-2b-instruct` | Q4_K_M | 1.44 GB | Parameterized SQL query generator and JSON schema validator. |
| **ARGUS** | Desktop Vision Eye | `Qwen2.5-VL-3B-Instruct` | Q4_K_M | 2.10 GB | Real-time UI bounding boxes, coordinates, and document OCR. |

---

### Tier 3: Real-Time Audio, VAD & Ambient Wake-Word

*Runs CPU-first with ~1-3% CPU overhead and 0 MB VRAM footprint.*

| Component | Model Name | File Path | Format | Size | Latency |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Voice Activity Detection** | Silero VAD v5 | `audio/vad/silero_vad.onnx` | ONNX | 2.2 MB | <1ms |
| **Acoustic Wake-Word** | openWakeWord (`Hey COPPER`) | `wakeword/hey_copper.onnx` | ONNX | 1.2 MB | <5ms |
| **Neural TTS Engine** | Kokoro-82M ONNX + Voice Bank | `audio/tts/kokoro-v0_19.onnx` + `voices.bin` | ONNX Float16 | 315 MB | <80ms |
| **Offline Speech-To-Text** | Whisper Large v3 Turbo | `audio/whisper/ggml-large-v3-turbo.bin` | GGML Q8 | 833 MB | <250ms |

---

### Tier 4: Memory Embeddings & Semantic Reranking

| Component | Model Name | Quantization | Size | Role in ChromaDB / Epistemic Memory |
| :--- | :--- | :---: | :---: | :--- |
| **Vector Memory Embeddings** | `nomic-embed-text-v1.5` | Q4_K_M | 80.2 MB | 8192-token dense semantic embeddings for long-term memory. |
| **Cross-Encoder Reranker** | `bge-reranker-v2-m3` | Q4_K_M | 418 MB | Top-k semantic re-ranking for ultra-precise memory retrieval. |
| **Context Embeddings** | `ModernBERT-base` | Q4_K_M | 80.2 MB | Fast transformer embeddings for local document chunks. |

---

### Tier 5: 100% Offline Local Image Studio (PICASSO)

| Engine | Model Artifact | Format | Size | Performance |
| :--- | :--- | :---: | :---: | :--- |
| **PICASSO Fast Diffusion** | `sd_turbo.safetensors` | Safetensors / UNet | 5.21 GB | 1-step real-time local image generation on RTX 5060 (<0.8s per 512x512 image). |

---

## 4. Hardware VRAM Discipline (8GB RTX 5060 Budget)

```
+-------------------------------------------------------------+
|              RTX 5060 8GB VRAM ALLOCATION MAP               |
+-------------------------------------------------------------+
| [0.0 - 0.94 GB] Resident Reflex Router (Qwen2.5 1.5B)       |
| [0.94 - 6.40 GB] Dynamic Heavyweight Slot (1 active 14B)    |
| [6.40 - 7.10 GB] Quantized KV Cache (q4_0 / 4096 tokens)    |
| [7.10 - 8.00 GB] OS / Display Driver & CUDA Headroom Buffer |
+-------------------------------------------------------------+
```

1. **Idle State**: Only the resident mini router (~0.94 GB VRAM) remains pinned (`keep_alive: -1`).
2. **Active Turn**: Router routes user prompt to the appropriate 14B specialist (e.g. VULCAN Coding).
3. **Execution**: The 14B model loads in ~5.2 GB VRAM (offloading 44/49 layers to GPU, remainder to system RAM), generating at >20 tokens/second.
4. **Post-Turn Sweep**: If no follow-up occurs within 60s, `ModelTierManager` issues eviction, restoring VRAM to <1.0 GB.
