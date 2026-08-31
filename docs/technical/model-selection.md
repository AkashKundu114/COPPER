# Model Selection & Orchestration Topology

## 1. Local Model Architecture Strategy

**C.O.P.P.E.R.** is engineered for ultra-low latency, 100% offline inference on modern consumer hardware (AMD Ryzen 9 / NVIDIA RTX 5060 Laptop GPU with 8GB VRAM).

To achieve state-of-the-art responsiveness without exceeding the 8GB VRAM constraint, C.O.P.P.E.R. implements a **Tiered Model Hierarchy** featuring **Lossless Abliterated LLMs**, an **Always-On Gatekeeper (keep_alive: -1)**, and **Transient Heavyweight Execution (auto-eviction after 60–240s)**.

---

## 2. Lossless Uncensoring Architecture (Weight Abliteration)

Standard open-weight models enforce rigid safety guardrails that result in false-positive refusals during security analysis, reverse engineering, automation scripting, and desktop OCR.

C.O.P.P.E.R. utilizes **Weight Abliteration** across its core and micro-agent tiers:
- **Orthogonal Direction Removal**: Refusal activation vectors are mathematically isolated across transformer layers and removed via orthogonal weight projection.
- **Zero Loss / No Catastrophic Forgetting**: Unlike fine-tuned "uncensored" models that degrade reasoning benchmarks, abliteration preserves 100% of the base model's MMLU, GSM8K, and HumanEval capability.
- **Dedicated Guardrail Layer**: Safety is decoupled from the base LLM and handled by specialized micro-subagents (`guardian` and `firewall`) that inspect inputs/outputs without refusal loops.

---

## 3. Master 34-Model Fleet Manifest

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
                                  │   Gatekeeper / Router  │
                                  │ (Qwen2.5 0.5B / 1B)    │ <--- Always-on (keep_alive: -1, ~770 MB VRAM)
                                  └───────────┬────────────┘
         ┌──────────────────┬─────────────────┼─────────────────┬──────────────────┐
         │                  │                 │                 │                  │
┌────────▼────────┐ ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐ ┌────────▼────────┐
│   Chat / Core   │ │ AXIS (Coding) │ │ KINESIS (Doc) │ │ FORGE (Auto)  │ │ OMNI (Reasoning) │
│ Llama-3.1 8B    │ │ Qwen2.5 7B    │ │ Qwen2.5 7B    │ │ Mistral 7B    │ │ DeepSeek-R1 7B   │
│ (Abliterated)   │ │ (Abliterated) │ │ (Abliterated) │ │ (Abliterated) │ │ (Abliterated)    │
└────────┬────────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └────────┬─────────┘
         │                  │                 │                 │                  │
         └──────────────────┴────────┬────────┴─────────────────┴──────────────────┘
                                     │
       ┌─────────────────────────────┼─────────────────────────────┐
       │                             │                             │
┌──────▼───────┐             ┌───────▼───────┐             ┌───────▼───────┐
│ Vision Agent │             │ Image Studio  │             │ 14 Specialized│
│ Qwen2.5-VL   │             │ PICASSO       │             │ Micro-Sub     │
│ 7B & 3B      │             │ SD-Turbo      │             │ Agents        │
└──────────────┘             └───────────────┘             └───────────────┘
```

---

### Tier 1: Primary Core Heavyweights (7B – 8B Abliterated)

*Loaded on-demand into GPU VRAM; managed by `ModelTierManager` with automatic idle eviction after 60s–240s.*

| Agent / Role | Model Name | Quantization | Size | Purpose & Specialization |
| :--- | :--- | :---: | :---: | :--- |
| **CHAT Orchestrator** | `Meta-Llama-3.1-8B-Instruct-abliterated` | Q4_K_M | 4.58 GB | Primary conversational companion, multi-turn dialogue, emotional resonance. |
| **AXIS Coding Agent** | `Qwen2.5-Coder-7B-Instruct-abliterated` | Q4_K_M | 4.36 GB | Full-stack software engineering, reverse engineering, sandbox code execution. |
| **KINESIS Document Agent** | `Qwen2.5-7B-Instruct-abliterated` | Q4_K_M | 4.36 GB | High-speed multi-format document generation (PDF, Word, Markdown, Excel, LaTeX). |
| **FORGE Automation Agent** | `Mistral-7B-Instruct-v0.3-abliterated` | Q4_K_M | 4.07 GB | System command generation, desktop GUI control, task automation. |
| **OMNI Reasoning Agent** | `DeepSeek-R1-Distill-Qwen-7B-abliterated` | Q4_K_M | 4.36 GB | Deep chain-of-thought math proofs, logic puzzles, algorithm design. |

---

### Tier 2: Multimodal Vision Agents (3B & 7B)

| Agent / Role | Model Name | Quantization | Size | Capabilities |
| :--- | :--- | :---: | :---: | :--- |
| **IRIS Primary Vision** | `Qwen2.5-VL-7B-Instruct-abliterated` | Q4_K_M | 4.36 GB | Full-resolution screenshot analysis, architecture diagrams, document OCR. |
| **IRIS Fast UI / OCR** | `Qwen2.5-VL-3B-Instruct-abliterated` | Q4_K_M | 1.80 GB | Real-time 60fps UI bounding box tagging, button coordinates, fast text extraction. |

---

### Tier 3: 100% Offline Local Image Studio (PICASSO)

| Engine | Model Artifact | Format | Size | Performance |
| :--- | :--- | :---: | :---: | :--- |
| **PICASSO Fast Diffusion** | `sd_turbo.safetensors` | Safetensors / UNet | 4.86 GB | 1-step real-time local image generation on RTX 5060 (<0.8s per 512x512 image). |

---

### Tier 4: Real-Time Audio, VAD & Ambient Wake-Word

*Runs CPU-first with $\approx 1-3\%$ CPU overhead and 0 MB VRAM footprint.*

| Component | Model Name | File Path | Format | Size | Latency |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Voice Activity Detection** | Silero VAD v5 | `audio/vad/silero_vad.onnx` | ONNX | 2.2 MB | <1ms |
| **Acoustic Wake-Word** | openWakeWord (`Hey COPPER`) | `wakeword/hey_copper.onnx` | ONNX | 1.2 MB | <5ms |
| **Wake-Word Embedding** | openWakeWord Embeddings | `wakeword/embedding_model.onnx` | ONNX | 1.3 MB | <2ms |
| **Neural TTS Engine** | Kokoro-82M ONNX + Voice Bank | `audio/tts/kokoro-v0_19.onnx` + `voices.bin` | ONNX Float16 | 315 MB | <80ms |
| **Offline Speech-To-Text** | Whisper Large v3 Turbo | `audio/whisper/ggml-large-v3-turbo.bin` | GGML Q8 | 833 MB | <250ms |
| **TTS Fallback Voices** | Piper (`amy`, `ryan`) | `audio/tts/en_US-*.onnx` | ONNX | 120 MB | <50ms |

---

### Tier 5: Memory Embeddings & Semantic Reranking

| Component | Model Name | Quantization | Size | Role in ChromaDB / Epistemic Memory |
| :--- | :--- | :---: | :---: | :--- |
| **Vector Memory Embeddings** | `nomic-embed-text-v1.5` | Q4_K_M | 80.2 MB | 8192-token dense semantic embeddings for long-term user memory. |
| **Cross-Encoder Reranker** | `bge-reranker-v2-m3` | Q4_K_M | 418 MB | Top-k semantic re-ranking for ultra-precise memory retrieval. |
| **Context Embeddings** | `ModernBERT-base` | Q4_K_M | 80.2 MB | Fast transformer embeddings for local document chunks. |

---

### Tier 6: Specialized Micro-Subagents (360M – 3.8B)

| Micro-Agent | Base Architecture | Quantization | Size | Functional Responsibility |
| :--- | :--- | :---: | :---: | :--- |
| **`router`** | `Llama-3.2-1B-Instruct-abliterated` | Q4_K_M | 911 MB | Sub-40ms intent classification and agent dispatch. |
| **`firewall` / `gatekeeper`** | `Qwen2.5-0.5B-Instruct-abliterated` | Q4_K_M | 379 MB | PII masking, secret redaction, and instant wake-word confirmation. |
| **`guardian`** | `Llama-3.2-3B-Instruct-abliterated` | Q4_K_M | 2.08 GB | Decoupled safety verification and content validation. |
| **`memory`** | `SmolLM2-1.7B-Instruct-abliterated` | Q4_K_M | 1006 MB | Epistemic fact, preference, and relationship extraction. |
| **`summarizer`** | `Qwen2.5-1.5B-Instruct-abliterated` | Q4_K_M | 940 MB | Context compression and conversational turn summarizing. |
| **`coding_linter`** | `Qwen2.5-Coder-0.5B-Instruct-abliterated` | Q4_K_M | 379 MB | Instant AST syntax error and linter checking. |
| **`coding_micro`** | `Qwen2.5-Coder-1.5B-Instruct-abliterated` | Q4_K_M | 1.04 GB | Unit test generation, docstring creation, and small refactors. |
| **`shell_safety`** | `Qwen2.5-Coder-3B-Instruct-abliterated` | Q4_K_M | 1.80 GB | Shell command parameter validation and sandbox checks. |
| **`diagnostics`** | `DeepSeek-R1-Distill-Qwen-1.5B-abliterated` | Q4_K_M | 1.04 GB | Stack trace root-cause analysis and auto-patch generation. |
| **`schema`** | `granite-3.2-2b-instruct` | Q4_K_M | 1.44 GB | Strict JSON schema normalization and tool output parsing. |
| **`sql`** | `granite-3.2-2b-instruct` | Q4_K_M | 1.44 GB | Parameterized SQL query drafting and SQLite syntax checking. |
| **`git`** | `SmolLM2-360M-Instruct` | Q4_K_M | 258 MB | Git diff analysis and Conventional Commit message generation. |
| **`planner`** | `Falcon3-3B-Instruct` | Q4_K_M | 1.87 GB | Goal decomposition and hierarchical task graph roadmapping. |
| **`search`** | `Qwen2.5-3B-Instruct-abliterated` | Q4_K_M | 1.80 GB | Search query optimization and multi-source verification. |

---

## 4. Hardware VRAM Discipline (8GB RTX 5060 Budget)

```
+-------------------------------------------------------------+
|              RTX 5060 8GB VRAM ALLOCATION MAP               |
+-------------------------------------------------------------+
| [0.0 - 0.8 GB] Always-On Gatekeeper (Llama-3.2-1B / Qwen)   |
| [0.8 - 5.5 GB] Dynamic Transient Slot (7B/8B Core Agent)    |
| [5.5 - 6.5 GB] Context Window & KV Cache (4k-8k Tokens)     |
| [6.5 - 8.0 GB] OS / Display Driver & CUDA Overhead Buffer  |
+-------------------------------------------------------------+
```

1. **Idle State**: Only the Gatekeeper (~770 MB VRAM) remains pinned (`keep_alive: -1`).
2. **Active Turn**: Router routes user prompt to the appropriate 7B–8B specialist (e.g. AXIS Coding).
3. **Execution**: The 7B–8B model loads, executes in ~4.5 GB VRAM, streams the output, and is assigned an idle countdown timer.
4. **Post-Turn Sweep**: If no follow-up occurs within 60s–240s, `ModelTierManager` issues a `keep_alive: 0` call to evict the heavy model, restoring VRAM to <1.0 GB.
