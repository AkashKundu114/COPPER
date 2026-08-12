# C.O.P.P.E.R.

**Centralized Omnifunctional Personal Productivity and Execution Routine**
*"Your Personal AI Operating System"*

[![License: MIT](https://img.shields.io/badge/License-MIT-amber.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![Tauri v2](https://img.shields.io/badge/Tauri-v2-FFC107.svg)](https://tauri.app/)
[![Ollama](https://img.shields.io/badge/Ollama-100%25_Offline-black.svg)](https://ollama.ai/)

---

> **C.O.P.P.E.R.** is a persistent, adaptive, privacy-first personal AI operating environment. Designed to run **100% offline by default**, C.O.P.P.E.R. helps users plan, execute, code, and maintain routines over time — respecting user autonomy while protecting long-term interests, productivity, and privacy.

---

## 🌟 Key Features & Architectural Pillars

- 🔒 **100% Offline Local-First Environment:** Operates completely offline using local models via Ollama (`llama3.1:8b`, `qwen2.5-coder:14b`, `mistral:7b`). Zero cloud transmission occurs unless explicitly enabled by the user.
- 🛡️ **Guardian Alignment Framework (Levels 0–3):** Evaluates prompts against goals and schedule commitments. Operates as a guardian, not a dictator:
  - **Level 0 (Direct Execution):** Standard task request aligning with goals.
  - **Level 1 (Nudge / Suggestion):** Inline optimization tips during execution.
  - **Level 2 (Challenge / Friction):** Pauses risky or off-schedule actions via `GuardianChallengeModal` with evidence, confidence, and options ([Follow recommendation], [Proceed anyway], [Discuss]).
  - **Level 3 (Safety Boundary):** Halts destructive or dangerous commands cleanly.
- 💻 **Personal Desktop AI OS Layout:** Features a persistent 13-section navigation sidebar:
  - `Dashboard` | `Conversation` | `Today` | `Tasks` | `Projects` | `Memory` | `Agents` | `Activity` | `Insights` | `Self-Improvement` | `Security` | `Food/Nutrition` | `Settings`
- 🌐 **Global Top Bar Status Badges:** Displays real-time status indicators: `● Local` (Green local mode), `🔒 Private` (Local encryption active), `🎙 Ready` (Voice PTT status), and User Profile.
- 💡 **3-Layer State & Epistemic Memory Architecture:** Combines `state.json` (live session state), 14 relational SQLite tables, and ChromaDB vector embeddings for Fact ($C \ge 0.85$), Observation ($0.50 \le C < 0.85$), and Hypothesis ($0.10 \le C < 0.50$) memory typing.
- 🎙️ **Voice & Audio Privacy:** Push-to-talk, click-to-speak, voice equalizer speaking bar, explicit mic permissions, and output toggles (`Text only`, `Voice only`, `Text + Voice`).
- 🤖 **30 Agents mapped to 8 Pre-Trained Models:** Maps 30 specialized sub-agents across 8 pre-trained model pools via System Prompt Injection (eliminating LoRA training compute overhead).
- 🔄 **Self-Healing & Terminal Safety:** Automatic 3-stage retry and tool fallback engine. Terminal safety review for potentially destructive commands. Secrets masked (`sk-••••••••`).

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
| FASTAPI BACKEND (Python 3.11+ / 100% Offline Default)                             |
|                                                                                   |
|  +-------------------+      +--------------------+      +----------------------+  |
|  | Agent Router      | ---> | Guardian Engine    | ---> | Data Firewall        |  |
|  | (Pre-trained Pool)|      | (Levels 0 - 3)     |      | (PII Redaction)      |  |
|  +-------------------+      +--------------------+      +----------+-----------+  |
|                                                                    |              |
|  +-----------------------------------------------------------------+              |
|  v                                                                                |
|  +-------------------+      +--------------------+      +----------------------+  |
|  | Agent Orchestrator| ---> | Self-Healing Loop  | ---> | Pre-Trained Models   |  |
|  | (30 Specialized)  |      | (Fallback & Retry) |      | (Ollama / Local LLM) |  |
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
| SQLite Persistence     |  | Redis Cache & PubSub |  | ChromaDB Vector Store       |
| (state.json + 14 DBs)  |  | (Session & Events)   |  | (Local Embedding Index)     |
+------------------------+  +----------------------+  +-----------------------------+
```

---

## 🚀 Quick Start Guide (100% Offline)

### Prerequisites
- **Git** 2.30+
- **Docker Desktop** (with Docker Compose v2+)
- **Python** 3.11+
- **Node.js** 18+ & **npm** 9+
- **Ollama** (for 100% local AI model execution)

### 1. Launch Services & Pull Local Models
```bash
git clone https://github.com/AkashKundu114/COPPER.git
cd COPPER

# Launch Postgres, Redis, ChromaDB, and Ollama
docker-compose up -d postgres redis chromadb ollama

# Pull 100% local pre-trained models
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:14b
ollama pull mistral:7b-instruct
```

### 2. Launch FastAPI Backend
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
*API Swagger Documentation is available locally at `http://localhost:8000/docs`.*

### 3. Launch Desktop UI (React + Vite)
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
*Open your browser locally at `http://localhost:5173`.*

---

## 📚 Documentation Suite

Comprehensive technical, architectural, and operational documentation is available in the [`docs/`](file:///d:/C.O.P.P.E.R/docs/README.md) directory:

- 📐 **Architecture:** [`ARCHITECTURE_OVERVIEW.md`](file:///d:/C.O.P.P.E.R/docs/architecture/ARCHITECTURE_OVERVIEW.md) | [`BACKEND_SCHEMA.md`](file:///d:/C.O.P.P.E.R/docs/architecture/BACKEND_SCHEMA.md) | [`DATA_FIREWALL_AND_SECURITY.md`](file:///d:/C.O.P.P.E.R/docs/architecture/DATA_FIREWALL_AND_SECURITY.md)
- ⚙️ **Technical:** [`TRD.md`](file:///d:/C.O.P.P.E.R/docs/technical/TRD.md) | [`IMPLEMENTATION_GUIDE.md`](file:///d:/C.O.P.P.E.R/docs/technical/IMPLEMENTATION_GUIDE.md) | [`MODEL_SELECTION.md`](file:///d:/C.O.P.P.E.R/docs/technical/MODEL_SELECTION.md)
- 💡 **Research:** [`PRD.md`](file:///d:/C.O.P.P.E.R/docs/research/PRD.md) | [`EPISTEMIC_MEMORY_RESEARCH.md`](file:///d:/C.O.P.P.E.R/docs/research/EPISTEMIC_MEMORY_RESEARCH.md) | [`GUARDIAN_INTERVENTION_RESEARCH.md`](file:///d:/C.O.P.P.E.R/docs/research/GUARDIAN_INTERVENTION_RESEARCH.md)
- 🚀 **Setup & Ops:** [`DEVELOPMENT_SETUP.md`](file:///d:/C.O.P.P.E.R/docs/setup/DEVELOPMENT_SETUP.md) | [`DEPLOYMENT_AND_INFRASTRUCTURE.md`](file:///d:/C.O.P.P.E.R/docs/setup/DEPLOYMENT_AND_INFRASTRUCTURE.md) | [`TROUBLESHOOTING.md`](file:///d:/C.O.P.P.E.R/docs/setup/TROUBLESHOOTING.md)
- 📊 **Diagrams:** [`SYSTEM_ARCHITECTURE.md`](file:///d:/C.O.P.P.E.R/docs/diagrams/SYSTEM_ARCHITECTURE.md) | [`APP_FLOW.md`](file:///d:/C.O.P.P.E.R/docs/diagrams/APP_FLOW.md) | [`STATE_MACHINES.md`](file:///d:/C.O.P.P.E.R/docs/diagrams/STATE_MACHINES.md)
- 🎨 **Design & UI:** [`UI_UX_BRIEF.md`](file:///d:/C.O.P.P.E.R/docs/ui_ux/UI_UX_BRIEF.md) | [`ACCESSIBILITY_AND_DESIGN.md`](file:///d:/C.O.P.P.E.R/docs/ui_ux/ACCESSIBILITY_AND_DESIGN.md)
- 🗓️ **Planning:** [`OPEN_QUESTIONS.md`](file:///d:/C.O.P.P.E.R/docs/planning/OPEN_QUESTIONS.md) | [`ROADMAP_AND_MILESTONES.md`](file:///d:/C.O.P.P.E.R/docs/planning/ROADMAP_AND_MILESTONES.md)

---

## 📄 License

C.O.P.P.E.R. is open-source software licensed under the [MIT License](file:///d:/C.O.P.P.E.R/LICENSE).
