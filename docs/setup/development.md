# C.O.P.P.E.R. Development Setup Guide

This guide walks you through setting up a complete local development environment for **C.O.P.P.E.R.** on Windows, macOS, or Linux.

---

## System Prerequisites

- **Operating System:** Windows 10/11, macOS 12+, or Ubuntu 22.04+
- **Python:** 3.11 or higher
- **Node.js:** 20+ LTS & npm 9+
- **Hardware Recommended:** NVIDIA RTX GPU with 8GB+ VRAM (or modern Apple Silicon / AMD APU)
- **Disk Space:** ~45 GB for full 26-model GGUF & ONNX offline suite

---

## Step-by-Step Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/AkashKundu114/COPPER.git
cd COPPER
```

### 2. Configure Python Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate environment:
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Windows (CMD):
.\.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate

# Install Python backend dependencies
pip install -r backend/requirements.txt
```

### 3. Initialize Database Schema
```bash
python scripts/db/init_db.py
python scripts/db/seed_data.py
```

### 4. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## Running the Application

### Option A: 1-Click Launch (Windows Dev Environment)
```powershell
.\scripts\dev\start_dev.bat
```
*Launches the FastAPI backend on port 8000 and opens the Electron Standalone Desktop application.*

### Option B: Manual Multi-Terminal Startup

**Terminal 1 — FastAPI Backend:**
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

**Terminal 2 — Electron Desktop App:**
```bash
cd frontend
npm run desktop
```

---

## Quality Gates & Test Suites

Always run the full test and benchmark suite before submitting PRs:

```bash
# 1. Run all 309 Pytest Unit & Integration Tests
python -m pytest tests/ -v

# 2. Run the 1,740-case Intent Routing & Guardian Benchmark
python backend/eval/benchmark.py

# 3. Verify Local Model Artifacts
python scripts/models/verify_models.py
```
