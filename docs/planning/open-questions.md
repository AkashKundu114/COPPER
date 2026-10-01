# C.O.P.P.E.R. Open Architectural Questions & Trade-Offs

This document tracks unresolved architectural inquiries, recently resolved design decisions, and core technical trade-offs across C.O.P.P.E.R. v3.0.0 and subsequent milestone releases.

---

## 1. Active Open Questions

### Question 1: Multi-Device Memory Synchronization
- **Status:** **OPEN** (Targeted for [v4.0.0 Phase 5](file:///d:/C.O.P.P.E.R/docs/planning/roadmap.md))
- **Issue:** How should epistemic user memory, knowledge graph entities, and conversation contexts synchronize across multiple desktop and mobile companion instances without requiring central cloud lock-in or unencrypted third-party data storage?
- **Options under evaluation:**
  - *Option A: Peer-to-Peer CRDT Sync via Local Network / WebRTC.* Fully decentralized state reconciliation using Conflict-free Replicated Data Types (CRDTs) over mDNS or WebRTC signaling. Guarantees zero cloud reliance, but requires concurrent device presence or mesh relay topology.
  - *Option B: User-Owned Encrypted Cloud Storage Sync.* End-to-end client-side encrypted snapshots (AES-256-GCM / ChaCha20-Poly1305) synchronized to user-provided storage (S3-compatible, Google Drive, iCloud, or WebDAV) using a locally managed master key.
  - *Option C: Hybrid Store-and-Forward Relay.* Direct local LAN synchronization with fallback to an encrypted user-controlled relay server when devices are partitioned across networks.
- **Current Direction:** Option B / Hybrid approach is under active evaluation for the v4.0.0 Phase 5 roadmap. Protocol specifications and zero-knowledge key exchange schemes will be formalized during v3.x maintenance cycles.

---

## 2. Resolved Architectural Decisions (v3.0.0)

### Question 2: Local GPU Memory Pressure during Multi-Agent Swarms
- **Status:** **RESOLVED in v3.0.0**
- **Prior Issue:** Executing multi-agent swarms concurrently on consumer GPUs (8 GB – 16 GB VRAM) risked CUDA Out-Of-Memory (OOM) crashes and latency spikes caused by uncoordinated model swapping.
- **Adopted Resolution:** Implemented the Dynamic VRAM Pager in [`backend/app/ai/llm/vram_pager.py`](file:///d:/C.O.P.P.E.R/backend/app/ai/llm/vram_pager.py):
  - **Bounded Allocation Framework:** Treats GPU VRAM as a bounded memory space under a strict 8 GB baseline consumer constraint.
  - **Multi-Factor Weighted LRU Eviction:** Models are scored via:
    $$\text{Score}(M) = w_{\text{recency}} \cdot \text{RecencyScore}(M) + w_{\text{frequency}} \cdot \text{FrequencyScore}(M) + w_{\text{lookahead}} \cdot \text{LookaheadPriority}(M)$$
    Unpinned models with the lowest composite score are evicted (`keep_alive=0`) prior to allocating new frames.
  - **DAG Lookahead:** Inspects upcoming task nodes in planner (NEXUS) execution graphs to proactively protect or pre-warm impending agent models.
  - **Single 14B Multiplexing Slot:** Constrains heavyweight 14B sovereign models (`qwen2.5:14b`, `deepseek-r1:14b`, `phi4:14b`, `mistral-nemo:12b` at ~5.2–6.4 GB) to a single multiplexed execution slot, co-residing safely alongside resident mini-models (≤3B, ~0.36–1.8 GB) without OOM faults.

### Question 3: Background Reflection & Memory Consolidation Model
- **Status:** **RESOLVED in v3.0.0**
- **Prior Issue:** Continuous background thought cycles (epistemic extraction, knowledge graph consolidation, memory decay) risked evicting primary interactive models from VRAM or inducing user-visible response latency.
- **Adopted Resolution:** Assigned `SmolLM2-1.7B-Instruct` (`smollm2:1.7b`, ~0.98–1.00 GB VRAM) as the dedicated background reflection engine:
  - Powers **CHRONOS** (Epistemic Memory Consolidator) and **SPIDER** (DOM & Web Cleaner / Fact Extractor).
  - Maintained as a resident micro-agent (`keep_alive=-1`) or lightweight worker in [`backend/app/ai/orchestration/task_scheduler.py`](file:///d:/C.O.P.P.E.R/backend/app/ai/orchestration/task_scheduler.py).
  - Delivers high-throughput (~135+ T/s) epistemic fact classification, preference extraction, and vector embedding staging for ChromaDB without displacing active 14B reasoning models.

### Question 4: Self-Memory Privacy, Auditability & Retention Policy
- **Status:** **RESOLVED in v3.0.0**
- **Prior Issue:** Clarifying the retention boundaries, editability, and deletion mechanisms for automated epistemic inferences, self-reflections, and telemetry while guaranteeing strict user privacy sovereignty.
- **Adopted Resolution:** End-to-end data governance delivered through the **Security Center UI** and zero-trust Data Firewall:
  - **Granular Memory Audit:** Interactive inspection of all self-memory entities, user preference vectors, and agent operational trails.
  - **One-Click Encrypted Export:** User-driven export of all stored memories, interaction logs, and graph connections into client-side encrypted JSON files.
  - **Instant Permanent Purge (`delete-all`):** Synchronous, atomic deletion across all storage backends:
    1. Relational records in PostgreSQL / SQLite
    2. Dense semantic embeddings in ChromaDB vector collections
    3. Ephemeral cache entries and session states in Redis
  - Verified zero-residual retention upon operator-triggered purge directives.

### Question 5: Character Universality vs. Persona Voice Differentiation
- **Status:** **RESOLVED in v3.0.0**
- **Prior Issue:** Maintaining a consistent foundational character (direct, transparent, anti-sycophantic) across diverse agents without flattening specialized persona domains or diluting technical competence across the fleet (12 active agents + 5 roadmap targets).
- **Adopted Resolution:** Additive System Prompt Layering in [`BaseAgent`](file:///d:/C.O.P.P.E.R/backend/app/ai/agents/base.py) across the agent topology ([`frontend/src/constants/agents.ts`](file:///d:/C.O.P.P.E.R/frontend/src/constants/agents.ts)):
  - **Fleet Scope:**
    - **12 Implemented Active Agents ([`AgentType`](file:///d:/C.O.P.P.E.R/backend/app/core/constants.py#L7-L52)):** ATLAS (Chat), VULCAN (Coding), SCRIBE (Document), DAEMON (Automation), CHRONOS (Reminder/Memory), PROMETHEUS (Research), ARGUS (Vision), PICASSO (Image), RAPTOR (Web Search), DELTA (Campaign Intelligence), NEXUS (Planner), AEGIS (Guardian).
    - **5 Planned Roadmap Targets:** PSYCHE (Behavior), SOLIS (Nutrition), JUSTICIA (Evaluator), SYMPHONY (Swarm Orchestrator), ECHO (Voice).
  - **Additive Prompt Stacking:**
    1. *Base Character Core (Prepended):* Shared C.O.P.P.E.R. identity, epistemic humility, anti-sycophancy rules, and safety boundaries.
    2. *Domain Persona Directive (Appended):* Specialized role scope, communication cadence, and domain heuristics (e.g., DAEMON shell precision vs. VULCAN code architecture rigor).
    3. *Dynamic Schemas & Context (Injected):* Tool definitions, [GUARDIAN_GATED] policy constraints, and retrieved episodic memory context injected per turn.

---

## 3. Technical Trade-Off Decisions

| Subsystem | Chosen Solution | Alternative Considered | Trade-Off Rationale |
| :--- | :--- | :--- | :--- |
| **Visualizer Engine** | Pure SVG + CSS Animations / Framer Motion | WebGL / 3D Canvas | Eliminates GPU rendering contention with local LLM VRAM allocations; provides deterministic DOM testing and zero native dependency footprint. |
| **Local LLM Runtime** | Ollama API + `llama-cpp-python` GGUF Engine | vLLM / Raw C++ llama.cpp bindings | Enables universal cross-platform deployment on consumer hardware with standardized REST endpoints and quantized GGUF (IQ3_XS / Q4_K_M) execution. |
| **Vector Database** | ChromaDB (In-Process) | Pinecone / Qdrant / Milvus | Runs locally without cloud subscriptions, external network egress, or telemetry leakage; integrates cleanly with SQLite metadata storage. |
| **Audio Processing** | Kokoro-82M ONNX + Whisper Large v3 Turbo | Cloud Speech APIs (OpenAI / ElevenLabs) | Enables deterministic offline transcription and sub-300ms speech synthesis while preserving complete acoustic privacy. |
| **Constitutional Safety** | Offline Guardian Engine (Levels 0–3) | Cloud Content Moderation APIs | Enforces local action reversibility analysis, zero-trust PII masking, and friction index scoring without external network dependencies. |
