# Changelog

All notable changes to **C.O.P.P.E.R.** (Centralized Omnifunctional Personal Productivity and Execution Routine) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned / In Development
- **Multi-Device Epistemic Memory Sync:** Peer-to-peer end-to-end encrypted memory synchronization for multi-device desktop/mobile setups.
- **Custom Fine-Tuned LoRA Weights:** Specialized local fine-tuning scripts utilizing Unsloth for Llama 3.1 & Qwen 2.5 Coder models.
- **Native Mobile Companion App:** React Native / Flutter companion client for mobile schedule and routine nudges.

---

## [1.0.0] - 2026-08-12

### Architecture Reconciliation Release (v1.0.0 Major Milestone)

This major release consolidates five architectural passes, resolving legacy single-agent local specs into a persistent, 30-agent, guardian-aligned personal AI assistant.

### Added
- 🛡️ **Guardian Alignment Framework (Levels 0–3):** Evaluates user instructions against routines, energy fatigue, and long-term goals. Introduces `GuardianChallengeModal` for Level 2 interactive challenges and Level 3 safety boundaries.
- 🔒 **Zero-Trust Data Firewall:** Built-in scanner in `backend/app/core/data_firewall.py` detecting PII (API keys, SSNs, credit cards, emails). Anonymizes sensitive data into synthetic session tokens before sending payloads to cloud LLM providers.
- 💡 **Epistemic Memory Engine V2 (`memory_v2`):** Classifies user facts into Facts ($C \ge 0.85$), Observations ($0.50 \le C < 0.85$), and Hypotheses ($0.10 \le C < 0.50$). Implements Bayesian belief updates and temporal decay math:
  $$C(t) = C_0 \cdot e^{-\lambda_T \cdot \Delta t}$$
- ⚡ **30-Agent Radial Visualizer (`NeuralBrain.tsx`):** Interactive SVG ganglia map with 4 orbital tiers, real-time edge pulse animations, and deterministic 30-node spacing.
- 🔊 **Speaking Bar & Widget Rail:** Dynamic equalizer bar synchronizing text-to-speech timing, alongside always-on Clock, Weather, Calendar, and Network widgets.
- 🔄 **Self-Healing Execution Loop (`self_healing.py`):** Automated 3-stage retry and secondary tool/model fallback engine for failed agent tasks.
- 📜 **Security Center & Audit Log (`audit_log`):** Human-readable event trail with one-click encrypted JSON data export and instant permanent purge (`delete-all`).
- 📁 **Comprehensive Documentation Suite in `docs/`:**
  - `docs/architecture/`: `ARCHITECTURE_OVERVIEW.md`, `BACKEND_SCHEMA.md`, `DATA_FIREWALL_AND_SECURITY.md`
  - `docs/technical/`: `TRD.md`, `IMPLEMENTATION_GUIDE.md`, `MODEL_SELECTION.md`
  - `docs/research/`: `PRD.md`, `EPISTEMIC_MEMORY_RESEARCH.md`, `GUARDIAN_INTERVENTION_RESEARCH.md`
  - `docs/setup/`: `DEVELOPMENT_SETUP.md`, `DEPLOYMENT_AND_INFRASTRUCTURE.md`, `TROUBLESHOOTING.md`
  - `docs/diagrams/`: `SYSTEM_ARCHITECTURE.md`, `APP_FLOW.md`, `STATE_MACHINES.md`
  - `docs/ui_ux/`: `UI_UX_BRIEF.md`, `ACCESSIBILITY_AND_DESIGN.md`
  - `docs/planning/`: `OPEN_QUESTIONS.md`, `ROADMAP_AND_MILESTONES.md`

### Changed
- **Backend Architecture:** Refactored FastAPI backend from monolithic routes into a modular pipeline (`route` $\rightarrow$ `animate` $\rightarrow$ `respond` $\rightarrow$ `remember`).
- **Database Schema:** Upgraded SQLite/PostgreSQL models to support epistemic memory metadata, agent registry health endpoints, and audit trail indexing.
- **Frontend Theme:** Replaced standard dark theme with custom **Molten Copper** visual tokens (`#B87333`, `#FF5722`, `#4A3B32`, `#00E5FF`).

### Fixed
- Fixed SVG node overlap in radial layout map with deterministic 49px minimum pairwise spacing.
- Fixed label rotation tumbling by adding counter-rotating CSS transforms.
- Fixed CORS preflight headers for Vite dev server (`localhost:5173`) and Tauri desktop origin (`tauri://localhost`).

### Deprecated / Removed
- Deprecated legacy local-only single-agent specification files.
- Removed deprecated static documentation from previous un-reconciled drop.

---

## [0.9.0] - 2026-06-15

### Pre-Reconciliation Prototype
- Initial prototype featuring basic FastAPI backend, SQLite memory database, and flat Chat UI.
- Local LLM connection via Ollama for single-agent conversation.
