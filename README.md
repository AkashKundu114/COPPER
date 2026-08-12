# C.O.P.P.E.R.

**Centralized Omnifunctional Personal Productivity and Execution Routine**
*"Your Personal AI Operating System"*

> **Accomplished** a persistent, privacy-first personal AI operating environment **as measured by** 100% offline local execution with zero cloud egress, **by architecting** a multi-agent AI engine on top of local Ollama models (`llama3.1:8b`, `qwen2.5-coder:14b`, `mistral:7b`), ensuring user autonomy and protecting long-term interests.

[![License: MIT](https://img.shields.io/badge/License-MIT-amber.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://reactjs.org/)
[![TypeScript 6+](https://img.shields.io/badge/TypeScript-6.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![Tauri v2](https://img.shields.io/badge/Tauri-v2-FFC107.svg)](https://tauri.app/)
[![Ollama](https://img.shields.io/badge/Ollama-100%25_Offline-black.svg)](https://ollama.ai/)
[![CI Status](https://img.shields.io/badge/CI-Passing-brightgreen.svg)]()
[![Security Posture](https://img.shields.io/badge/Security-Red_Team_Audited-blue.svg)]()

---

## 🌟 Key Highlights & Benchmarks

- **Enforced zero PII leakage** to external models **as measured by** a 7-pattern regex firewall scanning every outbound payload, **by implementing** a classification-first Data Firewall with severity tiering (PUBLIC → SECRET) including IP, email, SSN, and credit card protection.
- **Protected user autonomy** through a 4-level Guardian Alignment Framework **as measured by** structured disagreement verdicts with evidence chains, **by classifying** actions against user goals and schedule commitments prior to execution.
- **Accelerated context retrieval** for adaptive learning **as measured by** instantaneous access to 3-Layer Epistemic Memory (Facts, Observations, Hypotheses), **by combining** SQLite relational state with ChromaDB semantic vector embeddings.
- **Streamlined agent orchestration** across 30 specialized sub-agents **as measured by** dynamic execution without LoRA compute overhead, **by leveraging** System Prompt Injection onto 8 pre-trained model pools.
- **Improved system resilience** and terminal safety **as measured by** autonomous recovery from execution errors, **by architecting** a 3-stage self-healing retry loop with fallback agents and tools.

---

## 🏗️ System Architecture Overview

```text
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
- **Node.js** 20+ & **npm** 9+
- **Ollama** (for local AI execution)

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

## 🔒 Security Posture & Threat Model

C.O.P.P.E.R. relies on a **Zero-Trust Data Firewall** and **Local-First Threat Model**.
- **100% Offline Default:** By design, the AI execution environment and data persistence layer reside purely on your local machine.
- **Authentication & Rate-Limiting:** For isolated local environments, auth is bypassed for frictionless development. In production deployments, Traefik proxy layers handle rate-limiting and TLS.
- **Red Team Security Review:** Subjected to rigorous internal auditing ensuring input validation, path traversal safety, and robust CORS configurations.

> [!WARNING]
> Do not expose the core FastAPI instance or WebSockets to the public internet without a reverse proxy handling proper authentication.

---

## 🧪 Code Quality & Testing

In alignment with **Microsoft Code Quality Practices**, C.O.P.P.E.R. implements strict CI/CD quality gates ensuring that the codebase is constantly in a healthier state.

- **Gate 1: Static Analysis & Linting** (Ruff for Python, Oxlint for TypeScript)
- **Gate 2: Security & Formatting** (Ruff format, strict TypeScript type checking)
- **Gate 3: Test Coverage** (Comprehensive Pytest suite focusing on core logic engines: Data Firewall, Guardian, Self-Healing)

---

## 🤝 Contributing Guidelines

We welcome contributions following these **Code Review & Etiquette Principles**:
1. **The "Healthier Codebase" Rule:** Every PR must leave the modified code in a cleaner state.
2. **Small, Atomic Pull Requests:** Keep PRs focused to simplify peer review.
3. **Prefix Non-Blocking Comments:** Use `Nit:` for minor style suggestions that shouldn't block a merge.
4. **Google XYZ Impact:** Include a Google XYZ statement in your PR description summarizing the change's technical or performance impact.

---

## 📚 Documentation Suite

Comprehensive technical, architectural, and operational documentation is available in the `docs/` directory:

- 📐 **Architecture:** `ARCHITECTURE_OVERVIEW.md` | `BACKEND_SCHEMA.md` | `DATA_FIREWALL_AND_SECURITY.md`
- ⚙️ **Technical:** `TRD.md` | `IMPLEMENTATION_GUIDE.md` | `MODEL_SELECTION.md`
- 💡 **Research:** `PRD.md` | `EPISTEMIC_MEMORY_RESEARCH.md` | `GUARDIAN_INTERVENTION_RESEARCH.md`
- 🚀 **Setup & Ops:** `DEVELOPMENT_SETUP.md` | `DEPLOYMENT_AND_INFRASTRUCTURE.md` | `TROUBLESHOOTING.md`
- 📊 **Diagrams:** `SYSTEM_ARCHITECTURE.md` | `APP_FLOW.md` | `STATE_MACHINES.md`
- 🎨 **Design & UI:** `UI_UX_BRIEF.md` | `ACCESSIBILITY_AND_DESIGN.md`
- 🗓️ **Planning:** `OPEN_QUESTIONS.md` | `ROADMAP_AND_MILESTONES.md`

---

## 📄 License

C.O.P.P.E.R. is open-source software licensed under the MIT License.
