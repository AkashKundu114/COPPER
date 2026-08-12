# C.O.P.P.E.R.

**Centralized Omnifunctional Personal Productivity and Execution Routine**

[![License: MIT](https://img.shields.io/badge/License-MIT-amber.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![Tauri v2](https://img.shields.io/badge/Tauri-v2-FFC107.svg)](https://tauri.app/)
[![Ollama](https://img.shields.io/badge/Ollama-Local_Inference-black.svg)](https://ollama.ai/)

---

> **C.O.P.P.E.R.** is a persistent, adaptive, guardian-style personal AI assistant designed to help users plan, execute, code, and maintain routines over time — respecting user autonomy while protecting long-term interests, productivity, and privacy.

---

## 🌟 Key Features & Architectural Pillars

- 🛡️ **Guardian Alignment Framework (Levels 0–3):** Evaluates prompts against user goals and schedule routines. Operates with graduated intervention levels:
  - **Level 0 (Direct Execution):** Standard task request aligning with goals.
  - **Level 1 (Nudge / Suggestion):** Executes while offering inline tips or schedule recommendations.
  - **Level 2 (Challenge / Friction):** Pauses risky late-night or high-impact actions and triggers `GuardianChallengeModal` for explicit user confirmation.
  - **Level 3 (Safety Boundary):** Halts destructive commands cleanly with clear safety explanations.
- 🔒 **Zero-Trust Data Firewall:** Ollama (local) is the default inference provider. External cloud calls (OpenAI, Claude) pass through a zero-trust Data Firewall that scans, classifies, and redacts sensitive PII (API keys, SSNs, emails) before data leaves your machine.
- 💡 **Epistemic Memory Engine:** Differentiates stored user memory into **Facts** ($C \ge 0.85$), **Observations** ($0.50 \le C < 0.85$), and **Hypotheses** ($0.10 \le C < 0.50$), each driven by Bayesian belief updates, evidence metrics, and temporal decay math.
- ⚡ **30 Hot-Swappable Versioned Agents:** Houses 30 domain-specialized agents (Planner, Coding, Automation, Research, Vision, etc.) visualised on an interactive, orbital SVG ganglia map (`NeuralBrain.tsx`). Supports versioning, health checks, and instant rollback.
- 🔄 **Self-Healing Execution Loop:** Retries failed tool/LLM calls with parameter adjustments and secondary tool/model fallbacks before ever surfacing an unrecovered error. All attempts land in the human-readable Security Center Audit Log.
- 🎨 **Molten Copper Design System:** Unique aesthetic featuring dark obsidian surfaces, copper wire glow transitions, animated equalizer speaking bars, and responsive widget rails.
- 🖥️ **Native Desktop & Web Ready:** Runs as a lightweight native desktop app via Tauri or as a modern SPA via React/Vite.

---

## 🏗️ System Architecture Overview

```
                                  +-----------------------+
                                  |   Tauri Desktop /     |
                                  |   React Web Frontend  |
                                  +-----------+-----------+
                                              |
                                   REST / WebSockets
                                              v
+-----------------------------------------------------------------------------------+
| FASTAPI BACKEND (Python 3.11+)                                                    |
|                                                                                   |
|  +-------------------+      +--------------------+      +----------------------+  |
|  | Agent Router      | ---> | Guardian Engine    | ---> | Data Firewall        |  |
|  | (Keyword / Vector)|      | (Levels 0 - 3)     |      | (PII Redaction)      |  |
|  +-------------------+      +--------------------+      +----------+-----------+  |
|                                                                    |              |
|  +-----------------------------------------------------------------+              |
|  v                                                                                |
|  +-------------------+      +--------------------+      +----------------------+  |
|  | Agent Orchestrator| ---> | Self-Healing Loop  | ---> | LLM Service Layer    |  |
|  | (30 Specialized)  |      | (Fallback & Retry) |      | (Ollama / Cloud API) |  |
|  +---------+---------+      +--------------------+      +----------+-----------+  |
|            |                                                       |              |
|            v                                                       |              |
|  +-------------------+                                             |              |
|  | Epistemic Learner |                                             |              |
|  | & Fact Engine     |                                             |              |
|  +---------+---------+                                             |              |
+------------|-------------------------------------------------------|--------------+
             |                                                       |
             v                                                       v
+------------------------+  +----------------------+  +-----------------------------+
| PostgreSQL / SQLite    |  | Redis Cache & PubSub |  | ChromaDB Vector Store       |
| (Memory, Registry, Logs)|  | (State, Live Events) |  | (Semantic Embedding Index)  |
+------------------------+  +----------------------+  +-----------------------------+
```

---

## 🛠️ Technology Stack

| Component | Technologies |
| :--- | :--- |
| **Backend Core** | Python 3.11+, FastAPI, Uvicorn, Gunicorn, Pydantic v2 |
| **Databases** | PostgreSQL 15 / SQLite (Relational), ChromaDB (Vector Store), Redis 7 (Cache & PubSub) |
| **Local LLM Engine** | Ollama (Llama 3.1 8B, Qwen 2.5 Coder, Mistral 7B) |
| **Cloud Integration** | OpenAI GPT-4o / Claude 3.5 Sonnet (via Zero-Trust Data Firewall) |
| **Frontend Framework**| React 18, TypeScript 5, Vite, Tailwind CSS, Zustand |
| **Desktop Shell** | Tauri v2 (Rust backend shell) |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Git** 2.30+
- **Docker Desktop** (with Docker Compose v2+)
- **Python** 3.11+
- **Node.js** 18+ & **npm** 9+
- **Ollama** (for local AI inference)

### 1. Clone Repository & Launch Services
```bash
git clone https://github.com/AkashKundu114/COPPER.git
cd COPPER

# Launch database, cache, vector store, and Ollama containers
docker-compose up -d postgres redis chromadb ollama

# Pull default local LLM models
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
```

### 2. Launch Backend (FastAPI)
```bash
cd backend
python -m venv venv

# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```
*API Swagger Documentation is available at `http://localhost:8000/docs`.*

### 3. Launch Frontend (React + Vite)
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
*Open your browser at `http://localhost:5173`.*

### 4. Build Desktop Executable via Tauri (Optional)
```bash
cd frontend
npm run tauri build
```

---

## 📚 Documentation Directory Suite

Comprehensive technical, architectural, and operational documentation is available in the [`docs/`](file:///d:/C.O.P.P.E.R/docs/README.md) directory:

- 📐 **Architecture:** [`ARCHITECTURE_OVERVIEW.md`](file:///d:/C.O.P.P.E.R/docs/architecture/ARCHITECTURE_OVERVIEW.md) | [`BACKEND_SCHEMA.md`](file:///d:/C.O.P.P.E.R/docs/architecture/BACKEND_SCHEMA.md) | [`DATA_FIREWALL_AND_SECURITY.md`](file:///d:/C.O.P.P.E.R/docs/architecture/DATA_FIREWALL_AND_SECURITY.md)
- ⚙️ **Technical:** [`TRD.md`](file:///d:/C.O.P.P.E.R/docs/technical/TRD.md) | [`IMPLEMENTATION_GUIDE.md`](file:///d:/C.O.P.P.E.R/docs/technical/IMPLEMENTATION_GUIDE.md) | [`MODEL_SELECTION.md`](file:///d:/C.O.P.P.E.R/docs/technical/MODEL_SELECTION.md)
- 💡 **Research:** [`PRD.md`](file:///d:/C.O.P.P.E.R/docs/research/PRD.md) | [`EPISTEMIC_MEMORY_RESEARCH.md`](file:///d:/C.O.P.P.E.R/docs/research/EPISTEMIC_MEMORY_RESEARCH.md) | [`GUARDIAN_INTERVENTION_RESEARCH.md`](file:///d:/C.O.P.P.E.R/docs/research/GUARDIAN_INTERVENTION_RESEARCH.md)
- 🚀 **Setup & Ops:** [`DEVELOPMENT_SETUP.md`](file:///d:/C.O.P.P.E.R/docs/setup/DEVELOPMENT_SETUP.md) | [`DEPLOYMENT_AND_INFRASTRUCTURE.md`](file:///d:/C.O.P.P.E.R/docs/setup/DEPLOYMENT_AND_INFRASTRUCTURE.md) | [`TROUBLESHOOTING.md`](file:///d:/C.O.P.P.E.R/docs/setup/TROUBLESHOOTING.md)
- 📊 **Diagrams:** [`SYSTEM_ARCHITECTURE.md`](file:///d:/C.O.P.P.E.R/docs/diagrams/SYSTEM_ARCHITECTURE.md) | [`APP_FLOW.md`](file:///d:/C.O.P.P.E.R/docs/diagrams/APP_FLOW.md) | [`STATE_MACHINES.md`](file:///d:/C.O.P.P.E.R/docs/diagrams/STATE_MACHINES.md)
- 🎨 **Design & UI:** [`UI_UX_BRIEF.md`](file:///d:/C.O.P.P.E.R/docs/ui_ux/UI_UX_BRIEF.md) | [`ACCESSIBILITY_AND_DESIGN.md`](file:///d:/C.O.P.P.E.R/docs/ui_ux/ACCESSIBILITY_AND_DESIGN.md)
- 🗓️ **Planning:** [`OPEN_QUESTIONS.md`](file:///d:/C.O.P.P.E.R/docs/planning/OPEN_QUESTIONS.md) | [`ROADMAP_AND_MILESTONES.md`](file:///d:/C.O.P.P.E.R/docs/planning/ROADMAP_AND_MILESTONES.md)

---

## 🤝 Contributing & Issue Tracking

We welcome community contributions!
- Please read [`ISSUES.md`](file:///d:/C.O.P.P.E.R/ISSUES.md) for our issue triage policy, bug report guidelines, and feature request templates.
- Report security vulnerabilities according to our [Security Policy](file:///d:/C.O.P.P.E.R/.github/SECURITY.md).
- Track version history and recent updates in [`CHANGELOG.md`](file:///d:/C.O.P.P.E.R/CHANGELOG.md).

---

## 📄 License

C.O.P.P.E.R. is open-source software licensed under the [MIT License](file:///d:/C.O.P.P.E.R/LICENSE).
