import os
from contextlib import asynccontextmanager

# Enforce NVIDIA dedicated GPU isolation
os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
os.environ.setdefault("HIP_VISIBLE_DEVICES", "")
os.environ.setdefault("ROCR_VISIBLE_DEVICES", "")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.ai.llm.model_tier_manager import model_tier_manager
from app.ai.orchestration.task_scheduler import start_scheduler, stop_scheduler
from app.api.routes import (
    agents,
    ambient,
    audit,
    automation,
    briefing,
    cache,
    chat,
    clipboard,
    documents,
    episodes,
    guardian,
    images,
    knowledge_graph,
    memory,
    orchestration,
    projects,
    reminders,
    routing_analytics,
    schedule,
    self_improvement,
    self_memory,
    system,
    tasks,
    telemetry_routes,
    training,
    vision,
    voice,
    wake,
    workflows,
    workspace,
)
from app.core.config import settings
from app.core.logger import logger
from app.core.telemetry import init_telemetry
from app.database.postgres import init_db
from app.database.redis_client import redis_close
from app.services.wake_word_service import wake_word_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    try:
        init_db()
        from app.ai.llm.prompt_manager import load_applied_patches_from_db

        load_applied_patches_from_db()
    except Exception as e:
        logger.warning(f"DB init failed (continuing): {e}")
    try:
        init_telemetry(app)
    except Exception as e:
        logger.warning(f"Telemetry init warning: {e}")
    start_scheduler()
    model_tier_manager.start()
    
    from app.ai.ambient.clipboard_monitor import clipboard_monitor
    clipboard_monitor.start()
    
    logger.info("COPPER backend ready")
    yield
    await wake_word_service.disable()
    
    from app.ai.ambient.clipboard_monitor import clipboard_monitor
    clipboard_monitor.stop()
    
    model_tier_manager.stop()
    stop_scheduler()
    await redis_close()
    logger.info("COPPER backend shutdown complete")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(self), microphone=(self)"
        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            if span and span.get_span_context().is_valid:
                response.headers["X-Trace-Id"] = f"{span.get_span_context().trace_id:032x}"
        except Exception:
            pass
        return response


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Centralized Omnifunctional Personal Productivity and Execution Routine",
    lifespan=lifespan,
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.include_router(ambient.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(clipboard.router, prefix="/api/v1")
app.include_router(cache.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")
app.include_router(wake.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")
app.include_router(knowledge_graph.router, prefix="/api/v1")
app.include_router(reminders.router, prefix="/api/v1")
app.include_router(automation.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(vision.router, prefix="/api/v1")
app.include_router(guardian.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(episodes.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(orchestration.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(self_memory.router, prefix="/api/v1")
app.include_router(self_improvement.router, prefix="/api/v1")
app.include_router(training.router, prefix="/api/v1")
app.include_router(routing_analytics.router, prefix="/api/v1")
app.include_router(workspace.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(schedule.router, prefix="/api/v1")
app.include_router(schedule.events_router, prefix="/api/v1")
app.include_router(briefing.router, prefix="/api/v1")
app.include_router(images.router, prefix="/api/v1")
app.include_router(telemetry_routes.router, prefix="/api/v1")

# Mount static files directory for generated image assets
os.makedirs(settings.IMAGE_OUTPUT_DIR, exist_ok=True)
app.mount("/generated", StaticFiles(directory=settings.IMAGE_OUTPUT_DIR), name="generated")


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "status": "online"}


@app.get("/health")
async def health():
    from app.ai.llm.ollama_client import ollama_client

    ollama_ok = await ollama_client.is_available()
    return {"status": "healthy", "ollama": ollama_ok, "version": settings.APP_VERSION}
