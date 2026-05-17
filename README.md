# C.O.P.P.E.R

## Centralized Omnifunctional Personal Productivity and Execution Routine

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi" />
  <img src="https://img.shields.io/badge/React-18-blue?logo=react" />
  <img src="https://img.shields.io/badge/Tauri-2.0-orange?logo=tauri" />
  <img src="https://img.shields.io/badge/Docker-Compose-blue?logo=docker" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
</div>

---

COPPER is a next-generation AI desktop productivity assistant inspired by JARVIS. It combines voice interaction, multi-agent AI, desktop automation, context memory, and smart reminders into a single sleek desktop application.

---

## ✅ Bug Fixes Applied (vs. Initial Release)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 1 | `langchain_manager.py` | `ChatOllama` imported from deprecated `langchain_community` | Moved to `langchain_ollama` package |
| 2 | `reminders.py` | `async` callback passed directly to sync APScheduler | Added sync wrapper + `run_coroutine_threadsafe` |
| 3 | `requirements.txt` | Missing `pyttsx3`, `pygetwindow`, `SpeechRecognition`, `langchain-ollama` | Added all missing dependencies |
| 4 | `useWebSocket.ts` | `thinking` event created a duplicate assistant message bubble | Removed duplicate `addMessage` call; single bubble created in `send()` |
| 5 | `Navbar.tsx` | Unused `Wifi`, `WifiOff` imports caused TS warnings | Removed |
| 6 | `Memory.tsx` | Unused `Upload`, `BarChart2` imports; Upload button not wired | Wired Upload button to `/memory/ingest` endpoint |
| 7 | `formatters.ts` | Empty `formatters()` export was dead code | Removed |

---

## Features

| Category | Capability |
|----------|-----------|
| **AI Chat** | Multi-agent routing (chat, coding, automation, reminder, research, vision) |
| **Voice** | Wake-word detection · Whisper STT · OpenAI / local TTS |
| **Automation** | Shell commands · App launching · File management · Browser control |
| **Memory** | ChromaDB vector store · Semantic search · Document ingestion |
| **Reminders** | Natural-language parsing · Recurring schedules (cron) · WS notifications |
| **Vision** | Screenshot capture · Tesseract OCR · GPT-4o / LLaVA image analysis |
| **LLM** | Ollama (local) + OpenAI (cloud), switchable per request |
| **Desktop** | Tauri 2.0 native wrapper for Windows / macOS / Linux |

---

## Tech Stack

```
Frontend  →  React 18 · TypeScript · Tailwind CSS · Framer Motion · Tauri 2
Backend   →  FastAPI · Python 3.11 · LangChain · LangGraph
AI        →  Ollama · OpenAI API · Whisper · LangChain-Ollama
Database  →  PostgreSQL · ChromaDB · Redis
Infra     →  Docker Compose · GitHub Actions · Nginx
```

---

## Project Structure

```
COPPER/
├── frontend/          React + Tauri desktop app
│   └── src/
│       ├── components/   chat · dashboard · voice · system
│       ├── pages/        Dashboard · Chat · Memory · Reminders · Automation · Settings
│       ├── hooks/        useWebSocket · useVoice · useMemory · useSystemStats
│       ├── services/     api · websocket · voiceService
│       └── store/        chatStore · settingsStore · voiceStore · systemStore
├── backend/
│   └── app/
│       ├── ai/           agents · llm · memory · voice · vision · orchestration
│       ├── api/          routes · websocket
│       ├── automation/   system · file · browser · workflow
│       ├── database/     postgres · redis · chromadb models
│       └── services/     chat · voice · memory · vision · automation
├── infrastructure/    nginx.conf
├── docs/              architecture.md
└── docker-compose.yml
```

---

## Prerequisites

| Tool | Minimum Version | Notes |
|------|----------------|-------|
| Docker | 24+ | Required for database services |
| Docker Compose | 2.20+ | Bundled with Docker Desktop |
| Node.js | 20 LTS | For frontend dev |
| Python | 3.11 | For backend dev |
| Rust | 1.77+ | Only for building the Tauri desktop app |
| Tesseract | 5.x | OCR — `apt install tesseract-ocr` / `brew install tesseract` |

> **GPU note:** Whisper runs on CPU by default (`compute_type="int8"`). A CUDA-capable GPU speeds up transcription significantly.

---

## Quick Start (Docker — Recommended)

### 1. Clone

```bash
git clone https://github.com/your-username/COPPER.git
cd COPPER
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and set at minimum:

```env
SECRET_KEY=replace-with-a-long-random-string

# Leave blank to use Ollama only (no cloud cost)
OPENAI_API_KEY=

# If you change these, keep them consistent with docker-compose.yml
POSTGRES_USER=copper
POSTGRES_PASSWORD=copperpass
POSTGRES_DB=copperdb
```

### 3. Start all services

```bash
docker-compose up --build
```

This starts:
- `copper-backend`  → http://localhost:8000
- `copper-frontend` → http://localhost:3000
- `copper-postgres` → postgres://localhost:5432
- `copper-redis`    → redis://localhost:6379
- `copper-chromadb` → http://localhost:8001
- `copper-ollama`   → http://localhost:11434

### 4. Pull an AI model (first run only)

```bash
docker exec -it copper-ollama ollama pull llama3
# For vision features:
docker exec -it copper-ollama ollama pull llava
```

### 5. Open COPPER

Navigate to **http://localhost:3000** in your browser — or build the desktop app (see below).

---

## Manual / Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit env file
cp .env.example .env

# Start only the infrastructure services
docker-compose up -d postgres redis chromadb ollama

# Run the backend
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend (web)

```bash
cd frontend
npm install
npm run dev          # → http://localhost:3000
```

### Frontend (Tauri desktop app)

```bash
# Ensure Rust is installed: https://rustup.rs
cd frontend
npm install
npm run tauri        # dev mode with hot-reload

# Production build
npm run tauri:build  # outputs to src-tauri/target/release/bundle/
```

---

## Configuration Reference

All backend config lives in `backend/.env`:

```env
# ── App ──────────────────────────────────────────────────────────────────────
SECRET_KEY=change-me-in-production-use-long-random-string
DEBUG=false

# ── PostgreSQL ───────────────────────────────────────────────────────────────
POSTGRES_USER=copper
POSTGRES_PASSWORD=copperpass
POSTGRES_DB=copperdb
POSTGRES_HOST=postgres        # use "localhost" for local dev
POSTGRES_PORT=5432

# ── Redis ────────────────────────────────────────────────────────────────────
REDIS_HOST=redis              # use "localhost" for local dev
REDIS_PORT=6379
REDIS_DB=0

# ── ChromaDB ─────────────────────────────────────────────────────────────────
CHROMA_HOST=chromadb          # use "localhost" for local dev
CHROMA_PORT=8000

# ── Ollama ───────────────────────────────────────────────────────────────────
OLLAMA_HOST=http://ollama:11434   # use "http://localhost:11434" for local dev
OLLAMA_MODEL=llama3

# ── OpenAI (optional) ────────────────────────────────────────────────────────
OPENAI_API_KEY=               # leave blank to use Ollama only
OPENAI_MODEL=gpt-4o

# ── Voice ────────────────────────────────────────────────────────────────────
WHISPER_MODEL=base            # tiny | base | small | medium | large
TTS_MODEL=tts-1
TTS_VOICE=alloy
WAKE_WORD=copper

# ── Frontend ─────────────────────────────────────────────────────────────────
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/api/v1
```

---

## Hosting on a VPS / Cloud Server

### Recommended: DigitalOcean / Linode / Hetzner droplet

**Minimum spec:** 4 vCPU · 8 GB RAM · 50 GB SSD (without local GPU)
**Recommended:** 8 vCPU · 16 GB RAM · 100 GB SSD (for Whisper + Ollama)

### Step-by-step deployment

#### 1. Provision the server

```bash
# Ubuntu 22.04 LTS — install Docker
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose plugin
sudo apt-get install docker-compose-plugin -y
```

#### 2. Clone and configure

```bash
git clone https://github.com/your-username/COPPER.git
cd COPPER
cp backend/.env.example backend/.env
nano backend/.env          # set SECRET_KEY, OPENAI_API_KEY, etc.
```

#### 3. Update CORS and API URLs

In `backend/.env`:
```env
# Replace with your actual domain or server IP
VITE_API_URL=https://copper.yourdomain.com/api/v1
VITE_WS_URL=wss://copper.yourdomain.com/api/v1
```

In `backend/app/core/config.py`, update `ALLOWED_ORIGINS`:
```python
ALLOWED_ORIGINS: list[str] = [
    "https://copper.yourdomain.com",
    "http://localhost:3000",
]
```

#### 4. Add Nginx reverse proxy

Create `/etc/nginx/sites-available/copper`:

```nginx
server {
    listen 80;
    server_name copper.yourdomain.com;

    # Redirect HTTP → HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name copper.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/copper.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/copper.yourdomain.com/privkey.pem;

    client_max_body_size 50M;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Backend REST
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }

    # WebSocket
    location /api/v1/chat/ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/copper /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Free SSL certificate
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d copper.yourdomain.com
```

#### 5. Deploy

```bash
docker compose up -d --build

# Pull the AI model
docker exec -it copper-ollama ollama pull llama3

# Check everything is running
docker compose ps
```

#### 6. (Optional) Set up systemd for auto-start

```bash
cat > /etc/systemd/system/copper.service << 'EOF'
[Unit]
Description=COPPER AI Assistant
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/root/COPPER
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable copper
sudo systemctl start copper
```

---

## Hosting on AWS

### Option A: EC2 (same as VPS above)

Use `t3.xlarge` (4 vCPU, 16 GB) or larger. Follow the VPS guide above.

### Option B: ECS + RDS + ElastiCache (production-grade)

1. Push images to ECR:
   ```bash
   aws ecr create-repository --repository-name copper-backend
   aws ecr create-repository --repository-name copper-frontend
   docker build -t copper-backend ./backend
   docker tag copper-backend:latest <aws_account>.dkr.ecr.<region>.amazonaws.com/copper-backend:latest
   docker push <aws_account>.dkr.ecr.<region>.amazonaws.com/copper-backend:latest
   ```

2. Create ECS Fargate cluster and task definitions pointing to the ECR images.

3. Replace local Postgres with **RDS PostgreSQL**, Redis with **ElastiCache**, and ChromaDB with a self-hosted EC2 instance or **Pinecone** (requires code change in `vector_store.py`).

4. Use **ALB** (Application Load Balancer) with sticky sessions for WebSocket support.

---

## Hosting on Google Cloud

```bash
# Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT/copper-backend ./backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT/copper-frontend ./frontend

# Deploy backend to Cloud Run
gcloud run deploy copper-backend \
  --image gcr.io/YOUR_PROJECT/copper-backend \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 4Gi \
  --cpu 2

# WebSocket note: Cloud Run supports WebSockets with HTTP/2
```

> **Important:** Cloud Run scales to zero. For persistent WebSocket connections and the Ollama model, use a **Compute Engine** VM instead.

---

## Useful Commands

```bash
# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart a single service
docker compose restart backend

# Open a shell in the backend container
docker exec -it copper-backend bash

# Database migrations (if schema changes)
docker exec -it copper-backend python -c "from app.database.postgres import init_db; init_db()"

# List available Ollama models
docker exec -it copper-ollama ollama list

# Pull a different model
docker exec -it copper-ollama ollama pull mistral
docker exec -it copper-ollama ollama pull codellama

# Backup PostgreSQL data
docker exec copper-postgres pg_dump -U copper copperdb > backup_$(date +%Y%m%d).sql

# Restore PostgreSQL backup
docker exec -i copper-postgres psql -U copper copperdb < backup_20260101.sql
```

---

## Switching AI Providers

In the COPPER **Settings** page, or in `backend/.env`:

| Provider | Config | Cost |
|----------|--------|------|
| Ollama (default) | `OLLAMA_MODEL=llama3` | Free (local) |
| OpenAI | Set `OPENAI_API_KEY` | Pay per token |
| Switch per-request | `provider` field in API | — |

To add a new model in Ollama:
```bash
docker exec -it copper-ollama ollama pull phi3        # small, fast
docker exec -it copper-ollama ollama pull deepseek-coder  # coding
docker exec -it copper-ollama ollama pull llava       # vision (required for image analysis)
```

Then update `OLLAMA_MODEL` in `.env` and restart the backend.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Connection refused` to backend | Run `docker compose ps` — ensure all containers are `Up` |
| Ollama timeout | Model not pulled yet: `docker exec -it copper-ollama ollama pull llama3` |
| ChromaDB error | Port conflict: change `CHROMA_PORT` in `.env` |
| WebSocket drops | Ensure Nginx `proxy_read_timeout` ≥ 86400 and `Upgrade`/`Connection` headers are set |
| OCR returns empty | Tesseract not installed in the container — the Dockerfile installs it; rebuild with `--no-cache` |
| Voice transcription slow | Use `WHISPER_MODEL=tiny` for speed; `WHISPER_MODEL=small` for accuracy |
| CORS error in browser | Add your domain to `ALLOWED_ORIGINS` in `config.py` |
| `ModuleNotFoundError: langchain_ollama` | Run `pip install langchain-ollama==0.1.1` |

---

## CI / CD

GitHub Actions workflows are included:

| Workflow | Trigger | Action |
|----------|---------|--------|
| `backend-ci.yml` | Push to `backend/**` | Install deps + placeholder tests |
| `frontend-ci.yml` | Push to `frontend/**` | `npm ci` + `npm run build` |
| `docker-build.yml` | Push to `main` | `docker-compose build` |

To add secrets for production deployments, go to **GitHub → Settings → Secrets and variables → Actions** and add:
- `DOCKER_HUB_USERNAME` / `DOCKER_HUB_TOKEN`
- `SSH_HOST` / `SSH_KEY` (for auto-deploy to your VPS)

---

## Future Goals

- [ ] Fully autonomous workflow chains (LangGraph)
- [ ] Cross-device synchronization
- [ ] AI scheduling with calendar integration
- [ ] Emotion-aware interaction via voice tone analysis
- [ ] Plugin marketplace for community agents
- [ ] Mobile companion app

---

## License

MIT License — Copyright (c) 2026 Akash Kundu

---

## Inspiration

Inspired by JARVIS while focusing on real-world productivity, local-first AI, and an open-source ethos.
