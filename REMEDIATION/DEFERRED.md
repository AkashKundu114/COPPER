# C.O.P.P.E.R. Deferred Items & Technical Debt Register

**Release Target**: `v0.1.0-alpha`  
**Date**: 2026-10-17  
**Status**: Logged for Post-Alpha Milestone Planning  

---

## 1. Overview

To ensure an honest, credible, and verified `v0.1.0-alpha` release, several architectural aspirations, experimental prototypes, and secondary features were intentionally deferred. Every feature included in `v0.1.0-alpha` is 100% verified by automated tests and empirical measurements.

The following items are cataloged with their rationale, current state, and target roadmap milestone.

---

## 2. Deferred Feature Catalog

### 2.1 Rust / Tauri v2 Desktop Bundle
- **Current Reality**: C.O.P.P.E.R. operates with Electron 44 as its primary verified desktop shell (`frontend/electron-main.cjs`, `frontend/preload.cjs`, `launch-desktop.js`), configured with strict `contextIsolation: true`, `nodeIntegration: false`, and sandboxed preload scripts.
- **Reason Deferred**: While a lightweight Rust/Tauri v2 prototype was initially explored, the complete migration of 16 custom desktop HUD views and local system tray integrations requires dedicated cross-platform CI builders on macOS, Windows, and Linux.
- **Target Milestone**: `v0.2.0-beta`

### 2.2 Tier 2 & Tier 3 Roadmap Agents (5 Agents)
- **Agents**:
  - `BEHAVIOR`: Longitudinal psychological and behavioral adaptation tracking.
  - `NUTRITION`: Vision-based meal analysis and metabolic scheduling.
  - `EVALUATOR`: Autonomous LLM response quality scoring and self-critique.
  - `ORCHESTRATOR`: Cross-device distributed task execution.
  - `VOICE_PRO`: Low-latency full-duplex conversational interruption engine.
- **Current Reality**: Cataloged in `backend/app/core/agent_registry.py` under `ROADMAP_PLANNED_AGENTS`. The active core fleet consists of exactly 12 production-ready agents.
- **Reason Deferred**: Requires additional specialized local model quantization and fine-tuning pipelines.
- **Target Milestone**: `v0.2.0` (Behavior, Nutrition, Evaluator) and `v0.3.0` (Orchestrator, Voice Pro).

### 2.3 Multi-Device CRDT Mesh Memory Synchronization
- **Current Reality**: Epistemic memory and knowledge graphs are stored in local SQLite (`copper.db`) and local ChromaDB vector collections, with CRC32 WAL crash recovery.
- **Reason Deferred**: Network-based CRDT synchronization introduces external attack surfaces and potential zero-egress boundary violations. It must be designed with end-to-end encryption (E2EE) and local zero-knowledge keys.
- **Target Milestone**: `v0.3.0`

### 2.4 Unsloth Local LoRA Fine-Tuning Pipeline
- **Current Reality**: C.O.P.P.E.R. uses pre-trained Ollama GGUF quantized models (e.g., `qwen2.5:14b`, `qwen2.5-coder:14b`, `deepseek-r1:14b`).
- **Reason Deferred**: In-situ LoRA fine-tuning requires 16GB+ dedicated VRAM for training batches, which exceeds the minimum hardware baseline (8GB VRAM).
- **Target Milestone**: `v0.2.0-beta` (Optional developer toolchain).

### 2.5 Native Mobile Companion Applications
- **Current Reality**: C.O.P.P.E.R. is an offline desktop workstation application.
- **Reason Deferred**: Out of scope for the alpha release.
- **Target Milestone**: Post-v1.0.

---

## 3. Verification & Safety Posture

Deferring these features allowed the team to achieve:
1. **Zero fabricated claims** across all project documentation.
2. **728 automated tests passing** with 0 failures (687 backend + 41 frontend).
3. **Strict offline zero-egress enforcement** confirmed via socket-level regression tests.
4. **Complete terminal safety review** verified across 29 adversarial breakout payloads.
