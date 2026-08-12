# C.O.P.P.E.R. Local Development & Setup Guide

---

## 1. Prerequisites & System Requirements

Before setting up C.O.P.P.E.R., ensure your system meets the following requirements:

### Hardware Requirements
- **CPU:** 4-core x64 / ARM64 processor (Intel i5/i7/i9, AMD Ryzen, Apple M-Series).
- **RAM:** Minimum 16 GB (32 GB recommended for running 14B local models).
- **GPU:** Optional but strongly recommended (NVIDIA GPU with 8GB+ VRAM, or Apple Silicon unified memory).
- **Storage:** 20 GB free disk space.

### Software Prerequisites
- **Git** 2.30+
- **Python** 3.11+
- **Node.js** 18+ & **npm** 9+
- **Docker Desktop** (with Docker Compose v2+)
- **Ollama** (for running local LLMs)
- **Rust Toolchain** (optional, required only for building Tauri desktop app binaries)

---

## 2. Step-by-Step Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/AkashKundu114/COPPER.git
cd COPPER
```

### Step 2: Start Supporting Services via Docker Compose
Launch PostgreSQL, Redis, ChromaDB, and Ollama containers:

```bash
docker-compose up -d postgres redis chromadb ollama
```

Verify all containers are healthy:
```bash
docker-compose ps
```

### Step 3: Pull Local LLM Models via Ollama
Pull the default local models for general reasoning and code synthesis:

```bash
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
```

### Step 4: Backend Setup (Python FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run Alembic migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The backend API documentation will be available at `http://localhost:8000/docs`.

### Step 5: Frontend Setup (React / TypeScript / Vite)

1. Open a new terminal window and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
4. Launch Vite development server:
   ```bash
   npm run dev
   ```
5. Open your browser and navigate to `http://localhost:5173`.

---

## 3. Running as Desktop App via Tauri (Optional)

To run C.O.P.P.E.R. inside the native Tauri desktop shell:

```bash
cd frontend
npm run tauri dev
```

To build a standalone production desktop executable:
```bash
npm run tauri build
```
The output installers (`.exe`, `.msi`, `.dmg`, or `.AppImage`) will be placed in `frontend/src-tauri/target/release/bundle/`.
