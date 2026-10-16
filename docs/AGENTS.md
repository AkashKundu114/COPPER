# Multi-Agent Registry & Model Pool Architecture

**Version**: `0.1.0-alpha`  
**Location**: `backend/app/core/agent_registry.py`  
**Test Suite**: `tests/test_agent_registry_counts.py`  

---

## 1. Executive Summary

C.O.P.P.E.R. operates with a data-driven, strictly typed **Multi-Agent Architecture**. Rather than using a single monolithic prompt, tasks are classified and dispatched by `TFP-Router` to domain-specialized agents. Each agent is mapped to a dedicated hardware model pool tier, ensuring optimal memory utilization on consumer GPUs.

The system defines exactly **12 Core Active Agents**, **8 Hardware Model Pools**, and **5 Roadmap Planned Agents**. This count is asserted deterministically in `tests/test_agent_registry_counts.py`.

---

## 2. Core Active Agents (12 Verified)

| Codename | ID / Enum | Tier | Domain | Default Local Model | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ATLAS** | `chat` | `MODEL_1_CORE` | General Reasoning | `qwen2.5:14b` | Conversational dialogue, intent synthesis, and context orchestration. |
| **VULCAN** | `coding` | `MODEL_2_CODE` | Software Architecture | `qwen2.5-coder-abliterated:14b` | Full-stack code generation, refactoring, and sandboxed test execution. |
| **SCRIBE** | `document` | `MODEL_1_CORE` | Document Synthesis | `phi4:14b` | Academic papers, multi-page PDFs, structured reports, and briefs. |
| **DAEMON** | `automation` | `MODEL_3_OS` | Desktop RPA | `mistral-nemo:12b` | Deterministic OS automation, window navigation, and background task queues. |
| **CHRONOS** | `reminder` | `MODEL_3_OS` | Time & Habits | `qwen2.5:14b` | Calendar synchronization, contextual nudges, and commitment tracking. |
| **PROMETHEUS** | `research` | `MODEL_1_CORE` | Epistemic Research | `deepseek-r1:14b` | Multi-turn deep research loops, hypothesis verification, and literature synthesis. |
| **ARGUS** | `vision` | `MODEL_4_VISION` | Visual Perception | `qwen2.5-vl:3b` | Multi-modal visual analysis, desktop screenshot OCR, and bounding box UI parsing. |
| **PICASSO** | `image` | `MODEL_4_VISION` | Image Generation | `sd_turbo` | Offline local 1-step diffusion image generation studio. |
| **HERMES** | `web_search` | `MODEL_5_WEB` | Private Metasearch | `qwen2.5:14b` | Local SearXNG-backed privacy-preserving internet metasearch and fact condensation. |
| **DELTA** | `campaign_intelligence`| `MODEL_1_CORE` | Telemetry Analytics | `deepseek-r1:14b` | Ad campaign telemetry analysis, conversion response modeling, and budget optimization. |
| **NEXUS** | `planner` | `MODEL_1_CORE` | Strategic Planning | `deepseek-r1:14b` | Complex instruction decomposition, task graph construction, and multi-agent DAG coordination. |
| **AEGIS** | `guardian` | `MODEL_1_CORE` | Safety Gatekeeper | `qwen2.5:1.5b` | Continuous friction scoring, action reversibility analysis, and safety boundary enforcement. |

---

## 3. Hardware Model Pool Tiers (8 Tiers)

Model pools allocate GPU VRAM dynamically to avoid CUDA out-of-memory errors:

1. `MODEL_1_CORE`: High-capacity reasoning engine (`qwen2.5:14b`, `deepseek-r1:14b`).
2. `MODEL_2_CODE`: Code-specialized LLM (`qwen2.5-coder:14b`).
3. `MODEL_3_OS`: Low-latency deterministic automation & habit engine (`mistral-nemo:12b`, `smollm2:1.7b`).
4. `MODEL_4_VISION`: Multimodal vision-language & latent diffusion (`qwen2.5-vl:3b`, `sd-turbo`).
5. `MODEL_5_WEB`: Fact-condensation and search summarization engine.
6. `MODEL_6_AUDIO`: Neural acoustic TTS and speech transcription (`kokoro-82m`, `whisper-large-v3-turbo`).
7. `EMBEDDING_POOL`: Local CPU/GPU sentence embeddings for ChromaDB vector search.
8. `WAKEWORD_POOL`: Real-time acoustic wake-word listener (`openwakeword` running on CPU).

---

## 4. Roadmap Planned Agents (5 Tier 2/3 Agents)

These agents are designed and specified in `ROADMAP_PLANNED_AGENTS`, scheduled for future releases:

1. **PSYCHE** (`behavior`): Circadian rhythms, fatigue modeling, and user behavioral preference optimization.
2. **SOLIS** (`nutrition`): Biometric intake tracking, meal scheduling, and cognitive health correlations.
3. **JUSTICIA** (`evaluator`): Autonomous hallucination verification, rubric scoring, and synthetic output judging.
4. **SYMPHONY** (`orchestrator`): High-density dynamic subagent swarming and consensus aggregation.
5. **ECHO** (`voice`): Sub-300ms bidirectional voice conversation with barge-in detection.
