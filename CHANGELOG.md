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

## [1.1.0] - 2026-08-13

### Security, Quality, & Documentation Overhaul

> **Accomplished** a production-ready CI/CD and security baseline **as measured by** passing a strict Red Team security audit and zero build failures on main, **by implementing** Microsoft code quality practices, a robust Pytest suite, and expanding the Zero-Trust Data Firewall.

### Added
- **Comprehensive Test Suite:** Added backend test coverage for Data Firewall, Guardian, Self-Healing, and Validators using `pytest`.
- **Automated Quality Gates:** Integrated `ruff` (Python) and `oxlint` with strict `tsc` checks into GitHub Actions CI workflows.
- **PR Template:** Enforced the Google XYZ formula for all open-source contributions.

### Changed
- **Documentation:** Rewrote `README.md` and `CHANGELOG.md` using the Google XYZ impact formula to clearly communicate architectural value.
- **Data Firewall:** Upgraded the PII redaction engine to identify and scrub **Social Security Numbers (SSNs)** and **Credit Card numbers** before external egress.

### Fixed
- **Routing & Validation:** Fixed a critical return-type mismatch in `validators.py` and a double `/api` prefix in `memory.py`.
- **Audit Trails:** Corrected mislabeled disablement events in `agents.py` audit logs.
- **CORS Hardening:** Restricted CORS middleware in `main.py` to explicit methods and headers, preventing unauthorized cross-origin requests.

---

## [1.0.0] - 2026-08-12

### Architecture Reconciliation Release (v1.0.0 Major Milestone)

This major release consolidates five architectural passes, resolving legacy single-agent local specs into a persistent, 30-agent, guardian-aligned personal AI assistant.

### Added
- **Guardian Alignment Framework (Levels 0–3):** Evaluates user instructions against routines, energy fatigue, and long-term goals. Introduces `GuardianChallengeModal` for Level 2 interactive challenges and Level 3 safety boundaries.
- **Zero-Trust Data Firewall:** Built-in scanner in `backend/app/core/data_firewall.py` detecting PII (API keys, SSNs, credit cards, emails). Anonymizes sensitive data into synthetic session tokens before sending payloads to cloud LLM providers.
- **Epistemic Memory Engine V2 (`memory_v2`):** Classifies user facts into Facts ($C \ge 0.85$), Observations ($0.50 \le C < 0.85$), and Hypotheses ($0.10 \le C < 0.50$). Implements Bayesian belief updates and temporal decay math:
  $$C(t) = C_0 \cdot e^{-\lambda_T \cdot \Delta t}$$
- **30-Agent Radial Visualizer (`NeuralBrain.tsx`):** Interactive SVG ganglia map with 4 orbital tiers, real-time edge pulse animations, and deterministic 30-node spacing.
- **Speaking Bar & Widget Rail:** Dynamic equalizer bar synchronizing text-to-speech timing, alongside always-on Clock, Weather, Calendar, and Network widgets.
- **Self-Healing Execution Loop (`self_healing.py`):** Automated 3-stage retry and secondary tool/model fallback engine for failed agent tasks.
- **Security Center & Audit Log (`audit_log`):** Human-readable event trail with one-click encrypted JSON data export and instant permanent purge (`delete-all`).
- **Comprehensive Documentation Suite in `docs/`:**
  - `docs/architecture/`: `overview.md`, `schema.md`, `security.md`, `voice-activation.md`
  - `docs/technical/`: `trd.md`, `implementation.md`, `model-selection.md`
  - `docs/research/`: `prd.md`, `epistemic-memory.md`, `guardian.md`, `whitepaper.md`
  - `docs/setup/`: `development.md`, `deployment.md`, `models.md`, `troubleshooting.md`
  - `docs/diagrams/`: `system-architecture.md`, `app-flow.md`, `state-machines.md`
  - `docs/ui_ux/`: `design-brief.md`, `interface-spec.md`, `accessibility.md`
  - `docs/planning/`: `open-questions.md`, `roadmap.md`
  - `docs/`: `benchmarks.md`, `README.md`

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
