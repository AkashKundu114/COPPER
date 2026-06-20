# COPPER — Industrial Grade Upgrade Guide

> Covers: reliability hardening, production Docker, Kubernetes deployment, and fine-tuning pipeline for all 6 model profiles.

---

## 1. Immediate Hardening (Do Before Anything Else)

### 1.1 Database Migrations — Add Alembic

The current `init_db()` with `create_all()` is a dev-only pattern. In production, schema changes destroy data.

```bash
cd backend
pip install alembic
alembic init alembic
```

`alembic/env.py` — point at your models:
```python
from app.database.postgres import Base
from app.database.models import history, memory, reminders, user  # noqa
target_metadata = Base.metadata
```

Generate and run migrations:
```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### 1.2 Structured Logging

Replace the current file logger with JSON output so log aggregators (Loki, CloudWatch) can parse it.

```bash
pip install structlog python-json-logger
```

`backend/app/core/logger.py`:
```python
import structlog, logging, sys

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger("copper")
```

### 1.3 Prometheus Metrics Endpoint

```bash
pip install prometheus-fastapi-instrumentator
```

`backend/app/main.py` — add after `app = FastAPI(...)`:
```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

Custom metrics for LLM latency (add to each agent):
```python
from prometheus_client import Histogram, Counter
llm_latency = Histogram("copper_llm_latency_seconds", "LLM response time", ["agent", "provider"])
llm_errors  = Counter("copper_llm_errors_total", "LLM errors", ["agent", "provider"])
```

### 1.4 Rate Limiting

```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# On route:
@router.post("/message")
@limiter.limit("30/minute")
async def send_message(request: Request, req: ChatRequest, ...):
```

### 1.5 Sentry Error Tracking

```bash
pip install sentry-sdk[fastapi]
```

```python
import sentry_sdk
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
)
```

### 1.6 Secrets — Never in Code

Rotate `SECRET_KEY` in production. Use environment variable injection via your platform:

```bash
# Generate a real key
python -c "import secrets; print(secrets.token_hex(64))"
```

Add to `backend/app/core/config.py`:
```python
SECRET_KEY: str  # NO default value — forces explicit env var in prod
```

### 1.7 Health Check Improvements

Add deep health check that verifies all dependencies:

```python
@app.get("/health/deep")
async def deep_health():
    checks = {}
    # PostgreSQL
    try:
        db = next(get_db()); db.execute(text("SELECT 1")); checks["postgres"] = "ok"
    except Exception as e: checks["postgres"] = f"error: {e}"
    # Redis
    try:
        r = await get_redis(); await r.ping(); checks["redis"] = "ok"
    except Exception as e: checks["redis"] = f"error: {e}"
    # Ollama
    checks["ollama"] = "ok" if await ollama_client.is_available() else "unavailable"
    
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
```

---

## 2. Production Docker Setup

See `docker-compose.prod.yml` (included in this package). Key differences from dev:

| Concern | Dev | Prod |
|---|---|---|
| Secrets | `.env` file | Docker secrets / env injection |
| Logging | stdout | JSON → Loki |
| Replicas | 1 each | 2+ for stateless services |
| Resource limits | None | CPU + memory capped |
| TLS | None | Traefik handles termination |
| Volumes | anonymous | Named with backup policy |
| Ollama | Shared | GPU-pinned with resource reservation |

### Multi-Stage Backend Dockerfile

Replace `backend/Dockerfile` with:

```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
RUN groupadd -r copper && useradd -r -g copper copper
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev tesseract-ocr libgl1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM deps AS production
COPY --chown=copper:copper . .
USER copper
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "4", "--no-access-log"]
```

---

## 3. Kubernetes Deployment

See `kubernetes/copper-full-deployment.yaml` (included). Architecture overview:

```
Internet → Nginx Ingress → TLS termination
             ├── /        → frontend:3000 (Deployment, 2 replicas, HPA)
             └── /api     → backend:8000  (Deployment, 2 replicas, HPA)
                               ├── postgres:5432  (StatefulSet, PVC 20Gi)
                               ├── redis:6379     (StatefulSet, PVC 5Gi)
                               ├── chromadb:8000  (StatefulSet, PVC 10Gi)
                               └── ollama:11434   (StatefulSet, PVC 50Gi, GPU node)

Monitoring:
  prometheus:9090 → scrapes /metrics from backend
  grafana:3000    → dashboards
  loki:3100       → log aggregation from all pods
```

### GPU Node Pool Setup (GKE / EKS / Azure AKS)

**GKE:**
```bash
gcloud container node-pools create gpu-pool \
  --cluster copper-cluster \
  --machine-type n1-standard-8 \
  --accelerator type=nvidia-tesla-t4,count=1 \
  --num-nodes 1
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
```

**EKS:**
```bash
eksctl create nodegroup --cluster copper-cluster \
  --name gpu-nodes --node-type g4dn.xlarge \
  --nodes 1 --managed
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.15.0/deployments/static/nvidia-device-plugin.yml
```

### Helm Chart Structure (create this for real deployments)

```
helm/copper/
├── Chart.yaml
├── values.yaml          ← environment-specific overrides
├── values.prod.yaml
├── values.staging.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── backend/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── hpa.yaml
│   │   └── configmap.yaml
│   ├── frontend/
│   ├── databases/
│   │   ├── postgres-statefulset.yaml
│   │   ├── redis-statefulset.yaml
│   │   └── chromadb-statefulset.yaml
│   ├── ollama/
│   │   ├── statefulset.yaml  ← GPU request here
│   │   └── pvc.yaml
│   ├── monitoring/
│   │   ├── servicemonitor.yaml
│   │   └── dashboards/
│   └── ingress.yaml
└── charts/             ← subcharts: postgresql, redis (bitnami)
```

Install:
```bash
helm upgrade --install copper ./helm/copper \
  -f helm/copper/values.prod.yaml \
  --namespace copper --create-namespace \
  --set backend.image.tag=$(git rev-parse --short HEAD) \
  --set frontend.image.tag=$(git rev-parse --short HEAD)
```

---

## 4. CI/CD Pipeline

Add to `.github/workflows/deploy.yml`:

```yaml
name: Build → Test → Deploy
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository_owner }}/copper

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: test, POSTGRES_DB: testdb }
        options: --health-cmd pg_isready
      redis:
        image: redis:7
        options: --health-cmd "redis-cli ping"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: cd backend && pip install -r requirements.txt && pytest tests/ -v

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: ${{ github.actor }}, password: ${{ secrets.GITHUB_TOKEN }} }
      - uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: ${{ github.ref == 'refs/heads/main' }}
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-backend:${{ github.sha }}
      - uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: ${{ github.ref == 'refs/heads/main' }}
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-frontend:${{ github.sha }}

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-helm@v3
      - name: Deploy to production
        run: |
          helm upgrade --install copper ./helm/copper \
            --set backend.image.tag=${{ github.sha }} \
            --set frontend.image.tag=${{ github.sha }} \
            -f helm/copper/values.prod.yaml \
            --namespace copper --wait --timeout 5m
```

---

## 5. Fine-Tuning Guide Overview

See `finetune/README_FINETUNE.md` for the complete step-by-step instructions.

See `finetune/train.py` for the training script (Unsloth + QLoRA + TRL).

See `finetune/datasets/` for the 6 model training datasets.

### Hardware Requirements Per Model

| Model Profile | Base Model | Min VRAM | Recommended | Est. Time (500 examples) |
|---|---|---|---|---|
| Model 1 (14B) | Qwen2.5-14B Q4 | 24 GB | A100 40GB | 8-12 hrs |
| Model 2 (7B)  | Qwen2.5-Coder-7B | 16 GB | RTX 3090 | 3-4 hrs |
| Model 3 (3B)  | Qwen2.5-3B | 10 GB | RTX 3080 | 1-2 hrs |
| Model 4 (7B)  | Qwen2-VL-7B | 16 GB | RTX 3090 | 3-4 hrs |
| Model 5 (7B)  | Qwen2.5-7B | 16 GB | RTX 3090 | 3-4 hrs |
| Model 6       | Whisper/Kokoro | CPU only | CPU | No fine-tune needed |

Cloud alternatives: RunPod (A100 ~$1.89/hr), Lambda Labs, Google Colab Pro+

---

## 6. Production Monitoring Checklist

- [ ] Prometheus scraping `/metrics` on backend
- [ ] Grafana dashboard for: request rate, p95 latency, error rate, LLM response time
- [ ] Alert rules: error rate > 5%, p95 latency > 10s, pod crashlooping
- [ ] Loki log aggregation from all pods (structured JSON logs)
- [ ] PVC backup schedule (postgres, chromadb) via Velero or cron snapshot
- [ ] SSL certificate auto-renewal (cert-manager with Let's Encrypt)
- [ ] Network policies — only backend can talk to postgres/redis/chromadb
- [ ] PodDisruptionBudget — keep 1 backend replica during node drains
- [ ] Resource quotas per namespace
- [ ] Regular `ollama pull` cron to keep models updated

---

## 7. Performance Tuning

### Backend
- Increase `uvicorn --workers` to `2 × CPU_cores + 1`
- Add `--limit-concurrency 100` to prevent overload
- Use `asyncpg` instead of `psycopg2` for async postgres
- Tune SQLAlchemy pool: `pool_size=20, max_overflow=40`

### Ollama
- Set `OLLAMA_NUM_PARALLEL=1` (enforce sequential)
- Set `OLLAMA_MAX_LOADED_MODELS=1` (prevent memory swaps)
- Pin Ollama to GPU node with `nodeSelector`

### Redis
- Enable AOF persistence for durability
- Set `maxmemory-policy allkeys-lru`
- Tune `chat_history` TTL to 48h (reduce `ContextEngine.SESSION_TTL` if memory-constrained)

### ChromaDB
- Enable `allow_reset: false` in production
- Use persistent storage with NVMe-backed PVC
- Set `chroma_server_cors_allow_origins` to only your backend's URL
