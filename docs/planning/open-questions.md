# C.O.P.P.E.R. Open Architectural Questions & Trade-Offs

---

## 1. Active Open Questions

### Question 1: Multi-Device Memory Synchronization
- **Issue:** How should epistemic user memory sync across multiple desktop/mobile instances without central cloud lock-in?
- **Options under evaluation:**
  - *Option A:* Peer-to-peer CRDT sync via encrypted local network WebRTC.
  - *Option B:* User-owned cloud bucket sync (S3 / Google Drive / iCloud) encrypted via local master key.
- **Current Status:** Option B under research for Phase 3 roadmap.

### Question 2: Local GPU Memory Pressure during Multi-Agent Swarms
- **Issue:** When multiple specialized agents run concurrently, reloading model weights into Ollama VRAM creates latency spikes.
- **Options under evaluation:**
  - *Option A:* Single universal 8B base model fine-tuned with LoRA adapters per agent tier.
  - *Option B:* Quantized sub-models permanently pinned in VRAM using Ollama `keep_alive`.
- **Current Status:** Option A selected for V1 release.

### Question 3: Background Reflection Cycle Model Choice
- **Issue:** Dedicated small local model (`subagents.summarizer` e.g. Qwen2.5-1.5B) vs. reusing whatever model is already warm in Ollama's `keep_alive` window to prevent GPU VRAM swapping during background thought cycles.
- **Current Status:** Dedicated summarizer model configured with fallback to active warm model.

### Question 4: Self-Memory Privacy & Retention Policy
- **Issue:** Extent of user editability and deletion for `self_memory` vs `memory_v2`. Internal self-reflections and track records have different retention rationales than personal user data.
- **Current Status:** Individual entry resolution and inspection enabled in UI; full audit log deletion rules under review.

### Question 5: Character Universality vs Persona Voice Differentiation
- **Issue:** Balancing unified COPPER directness, uncertainty-honesty, and continuity across all 30 personas while preserving persona-specific technical traits (e.g. AXIS engineering terseness vs CYPHER dry analysis).
- **Current Status:** Additive layering implemented — base character prompt prepended to all agents, with mode-specific instructions appended.

---

## 2. Technical Trade-Off Decisions

| Topic | Chosen Solution | Alternative Considered | Trade-Off Rationale |
| :--- | :--- | :--- | :--- |
| **Visualizer Engine** | Pure SVG + CSS animations | WebGL / 3D Canvas | SVG is zero-dependency, lightweight, deterministic, and easily tested. |
| **Local LLM Server** | Ollama | vLLM / llama.cpp raw | Ollama provides simple model management and standardized API endpoints across platforms. |
| **Vector DB** | ChromaDB | Pinecone / Qdrant | ChromaDB runs locally in-process without requiring external cloud subscriptions. |
