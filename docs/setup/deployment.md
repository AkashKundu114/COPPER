# Production Deployment & Infrastructure Specification

---

## 1. Production Deployment Architecture

C.O.P.P.E.R. can be deployed in production as a self-hosted single-node container stack or multi-node Kubernetes cluster.

```
                           +-------------------------------+
                           |     Nginx Reverse Proxy       |
                           |  (SSL Termination & TLS 1.3)  |
                           +---------------+---------------+
                                           |
                  +------------------------+------------------------+
                  | /api & /ws                                      | / (Static Assets)
                  v                                                 v
   +------------------------------+                  +------------------------------+
   | FastAPI Application Pods     |                  | React Web Static Build       |
   | (Gunicorn + Uvicorn Workers) |                  | (Nginx Static Serve)         |
   +--------------+---------------+                  +------------------------------+
                  |
     +------------+------------+-----------------------+
     |                         |                       |
     v                         v                       v
+---------+               +---------+             +----------+
| Postgres|               | Redis   |             | ChromaDB |
+---------+               +---------+             +----------+
```

---

## 2. Docker Compose Production Config (`docker-compose.prod.yml`)

The production stack isolates database volumes, sets memory constraints, and configures healthchecks:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    restart: always
    environment:
      - DATABASE_URL=postgresql://copper_user:copper_pass@postgres:5432/copper_db
      - REDIS_URL=redis://redis:6379/0
      - CHROMADB_HOST=chromadb
      - CHROMADB_PORT=8000
      - OLLAMA_BASE_URL=http://ollama:11434
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_USER: copper_user
      POSTGRES_PASSWORD: copper_pass
      POSTGRES_DB: copper_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U copper_user -d copper_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

---

## 3. Environment Variables Reference

| Variable Name | Default | Required in Prod | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://...` | Yes | Relational database connection string. |
| `REDIS_URL` | `redis://localhost:6379` | Yes | Redis connection string for cache and pub/sub. |
| `OLLAMA_BASE_URL` | `http://localhost:11434`| Yes | URL of Ollama service instance. |
| `OPENAI_API_KEY` | `""` | Optional | Key for cloud model fallback (routed via Data Firewall). |
| `DATA_FIREWALL_STRICT` | `true` | Yes | Enforces PII redaction on all cloud requests. |
| `LOG_LEVEL` | `INFO` | Yes | Logging verbosity (`DEBUG`, `INFO`, `WARN`, `ERROR`). |
