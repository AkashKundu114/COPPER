# Research — Index

> **Documentation hub:** [docs/README.md](../README.md)

This folder collects research notes, design rationale, and open questions that inform the core specification but aren't themselves part of it. If a research note matures into a firm decision, its conclusion should be folded back into the relevant core document ([PRD](../PRD.md), [TRD](../TRD.md), etc.) with a link back here for context.

| Document | Status | Description |
|---|---|---|
| [architecture-alternatives.md](architecture-alternatives.md) | Deprecated (preserved) | The original cloud-hybrid architecture draft (FastAPI/LangChain/OpenAI/PostgreSQL/Redis/Docker) and why it was not adopted |
| [model-selection.md](model-selection.md) | Draft | Rationale for the six model profiles and their quantization/VRAM tradeoffs |
| [open-questions.md](open-questions.md) | Living | Tracked ambiguities and unresolved items across the documentation set |

---

## How to Add a Research Note

1. Create `docs/research/<topic>.md` with a `> **Status:** Draft` header.
2. Link it from this index.
3. Cross-link from any core document section it informs (e.g. a TRD section that references "see research note on X").
4. When the question is resolved, update the core document directly, change this note's status to `Resolved`, and leave a one-line pointer to where the resolution now lives.

---

## Currently Open Questions

The full living list is in [open-questions.md](open-questions.md). Highlights:

- **Duplicate `NEXUS` agent** in the 30-agent roster ([PRD §3, footnote 1](../PRD.md#3-the-30-agents--full-roster)) — needs resolution before `agent_profiles` is seeded.
- **LoRA hot-swap latency target** (<100ms, [TRD §7.5](../TRD.md#75-tr-05-lora-adapter-hot-swap)) is currently unverified against `llama.cpp`'s `lora-scale` parameter — see [Implementation Guide §18](../IMPLEMENTATION.md#18-known-limitations--mitigations).
- **Florence-2 / Ollama integration** — Florence-2 is not natively supported by Ollama and is currently planned as a separate HF Transformers subprocess; this affects the VRAM accounting in [TRD §6.2, Model 4](../TRD.md#62-the-6-model-specialist-architecture).
