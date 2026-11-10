# ADR-0001: Local-First Operating Philosophy and 8GB VRAM Constraint

## Status
**Accepted**

## Context
C.O.P.P.E.R. (Centralized Omnifunctional Personal Productivity and Execution Routine) is designed as a sovereign, private personal AI operating system created solely by Akash Kundu. Workstation hardware constraints require running on an NVIDIA RTX 5060 Laptop GPU equipped with strictly 8.0 GB of VRAM alongside an AMD Ryzen 9 8940HX CPU and 32 GB of system RAM.

Cloud-based LLM architectures often assume infinite VRAM or persistent multi-model hosting. Running multiple 7B, 12B, and 14B models concurrently on an 8GB GPU causes instant CUDA Out-Of-Memory (OOM) errors, driver crashes, and desktop stutter.

## Decision
1. **Local-First Airgap Primacy**: All primary reasoning, coding, memory indexing, and document synthesis must execute on local hardware via Ollama / quantized GGUF weights. Cloud LLMs are strictly forbidden as primary dependencies.
2. **Dynamic Model Paging & Hot-Swapping**:
   - One fast reflex "gatekeeper" model (`qwen2.5:1.5b`, ~0.94 GB VRAM) is pinned permanently in memory (`keep_alive=-1`).
   - Heavy models (`qwen2.5-coder:14b`, `deepseek-r1:14b`, `mistral-nemo:12b`) are loaded on-demand and tracked via `VRAMPager`.
   - When total VRAM allocation approaches 7.5 GB, the least-recently/lowest-priority model is automatically evicted with `keep_alive=0`.
3. **No Distributed Infrastructure on Desktop**: Personal desktop mode must remain lightweight (<250 MB Python RSS, zero Kubernetes or external cloud dependencies).

## Consequences
- **Positive**: Complete privacy, zero ongoing cloud API subscription costs, guaranteed operation in offline/airgapped environments, zero CUDA OOM panics.
- **Negative**: Model switching latency overhead (~1.5s to 3.5s) when transitioning between complex tasks requiring different model weights. Mitigated by DAG model-affinity batching and lookahead preemption.
