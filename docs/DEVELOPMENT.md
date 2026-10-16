# C.O.P.P.E.R. Developer Guide & Workflows

**Comprehensive Local Setup, Development Workflows, Testing, Formatting, and Debugging**

---

## 1. Prerequisites & Environment Requirements

| Dependency | Minimum Version | Recommended Version | Verification Command |
| :--- | :--- | :--- | :--- |
| **Python** | 3.11.x | 3.12.x / 3.14.x (64-bit) | `python --version` |
| **Node.js** | 20.x | 22.x / 24.x LTS | `node --version` |
| **npm** | 9.x | 10.x / 11.x | `npm --version` |
| **Ollama** | 0.3.x | 0.5.x+ | `ollama --version` |
| **Git** | 2.40+ | Latest | `git --version` |

---

## 2. Local Setup Guide

### 2.1 Clone & Environment Initialization
```bash
# Clone the repository
git clone https://github.com/AkashKundu114/COPPER.git
cd COPPER

# Copy the environment template
cp .env.example .env
```

### 2.2 Python Backend Setup
```bash
# Create dedicated virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate on Linux / macOS
# source .venv/bin/activate

# Install Python dependencies
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 2.3 Frontend & Electron Setup
```bash
cd frontend
npm install
cd ..
```

### 2.4 Local Model Acquisition (Ollama)
C.O.P.P.E.R. runs with local quantized models:
```bash
# Start Ollama service
ollama serve

# Pull baseline models
ollama pull qwen2.5:1.5b
ollama pull qwen2.5:8b
ollama pull qwen2.5-coder:1.5b
```

---

## 3. Running Development Servers

### Option A: All-in-One Desktop Mode
```bash
# Starts Vite dev server and launches Electron desktop window
cd frontend
npm run desktop
```

### Option B: Decoupled Backend & Frontend

**Terminal 1 — FastAPI Backend (Port 8000):**
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — React 19 Frontend (Port 5173):**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` in your browser.

---

## 4. Code Formatting & Linting

### Python (Ruff)
Ruff is configured in [`pyproject.toml`](file:///D:/C.O.P.P.E.R/pyproject.toml) with strict linting rules:
```bash
# Check code for lint violations
ruff check .

# Automatically apply safe fixes
ruff check --fix .

# Format Python files
ruff format .
```

### Frontend (Oxlint & TypeScript)
```bash
cd frontend

# Run Oxlint for fast AST analysis
npm run lint

# Run TypeScript compiler check
npm run build
```

---

## 5. Automated Testing Guide

COPPER maintains a strict **100% pass rate** requirement across all test suites.

### 5.1 Backend Pytest Suites
```bash
# Run all backend core & AI tests (644 tests)
python -m pytest tests/ -v

# Run backend microservices tests (32 tests)
python -m pytest backend/tests/ -v

# Run AI Red Team security & jailbreak tests
python -m pytest tests/security/test_ai_red_team.py -v

# Run AST sandbox security tests
python -m pytest tests/core/test_ast_validator.py -v

# Run agent contract & topology parity tests
python -m pytest tests/ai/test_agent_consistency.py -v
```

### 5.2 Frontend Vitest Suites
```bash
cd frontend

# Run Vitest component & accessibility tests (41 tests)
npm run test

# Run tests in watch mode during development
npm run test:watch

# Generate code coverage report
npm run test:coverage
```

### 5.3 End-to-End Testing (Playwright)
```bash
cd frontend
npx playwright test
```

---

## 6. Logs & Debugging

- **Application Logs:** [`data/logs/app/`](file:///D:/C.O.P.P.E.R/data/logs/app/)
- **Security & Guardian Audit Logs:** [`data/logs/security/`](file:///D:/C.O.P.P.E.R/data/logs/security/)
- **SQLite Database Inspection:**
  ```bash
  sqlite3 data/copper_memory.db "PRAGMA journal_mode;"
  sqlite3 data/copper_memory.db "SELECT count(*) FROM memory_entries;"
  ```
- **Local Telemetry Dashboard:** Access `http://localhost:5173/#/telemetry` for live GPU, VRAM, and RAM telemetry charts.
