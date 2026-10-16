import os
from contextlib import asynccontextmanager

# Set headless display mode for CI/headless environments
if not os.environ.get("DISPLAY"):
    os.environ["DISPLAY"] = ":99"

# Enforce NVIDIA dedicated GPU isolation
os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
os.environ.setdefault("HIP_VISIBLE_DEVICES", "")
os.environ.setdefault("ROCR_VISIBLE_DEVICES", "")

# Set matplotlib to use non-interactive backend before any GUI imports
try:
    import matplotlib

    matplotlib.use("Agg")
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.ai.llm.model_tier_manager import model_tier_manager
from app.ai.orchestration.task_scheduler import start_scheduler, stop_scheduler
from app.api.routes import (
    accountability,
    activation,
    agents,
    ambient,
    audit,
    briefing,
    cache,
    catalog,
    causal,
    chat,
    clipboard,
    code_review,
    cognitive,
    context_switch,
    continuity,
    documents,
    email,
    episodes,
    federated,
    guardian,
    images,
    knowledge_graph,
    meetings,
    memory,
    notifications,
    orchestration,
    personality,
    plugins,
    predictions,
    privacy,
    provenance,
    reminders,
    routing_analytics,
    schedule,
    self_improvement,
    self_memory,
    setup,
    skill_gaps,
    skills,
    sync,
    system,
    telemetry_routes,
    training,
    vision,
    voice,
    wake,
    workspace,
)
from app.api import campaign_routes
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

    # Robust shutdown sequence with individual error isolation
    try:
        await wake_word_service.disable()
    except Exception as e:
        logger.warning(f"Shutdown error in wake_word_service.disable: {e}")

    try:
        from app.ai.ambient.clipboard_monitor import clipboard_monitor

        clipboard_monitor.stop()
    except Exception as e:
        logger.warning(f"Shutdown error in clipboard_monitor.stop: {e}")

    try:
        model_tier_manager.stop()
    except Exception as e:
        logger.warning(f"Shutdown error in model_tier_manager.stop: {e}")

    try:
        stop_scheduler()
    except Exception as e:
        logger.warning(f"Shutdown error in stop_scheduler: {e}")

    try:
        from app.ai.image.diffusion_engine import diffusion_engine

        diffusion_engine.unload()
    except Exception as e:
        logger.warning(f"Shutdown error in diffusion_engine.unload: {e}")

    try:
        from app.ai.memory.vector_store import close_chroma_client

        close_chroma_client()
    except Exception as e:
        logger.warning(f"Shutdown error in close_chroma_client: {e}")

    try:
        await redis_close()
    except Exception as e:
        logger.warning(f"Shutdown error in redis_close: {e}")

    try:
        from app.database.postgres import close_db

        close_db()
    except Exception as e:
        logger.warning(f"Shutdown error in close_db: {e}")

    try:
        from app.core.telemetry import shutdown_telemetry

        shutdown_telemetry()
    except Exception as e:
        logger.warning(f"Shutdown error in shutdown_telemetry: {e}")

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


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Guards against memory exhaustion DoS by enforcing request body size ceilings."""

    MAX_STANDARD_SIZE = 10 * 1024 * 1024  # 10 MB for standard API calls
    MAX_UPLOAD_SIZE = 25 * 1024 * 1024  # 25 MB for document/vision uploads

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                is_upload = request.url.path.startswith(("/api/v1/documents", "/api/v1/vision", "/api/v1/images"))
                limit = self.MAX_UPLOAD_SIZE if is_upload else self.MAX_STANDARD_SIZE
                if length > limit:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "status": "error",
                            "error": "Payload Too Large",
                            "message": f"Request body ({length} bytes) exceeds configured size ceiling ({limit} bytes).",
                        },
                    )
            except ValueError:
                pass
        return await call_next(request)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Centralized Omnifunctional Personal Productivity and Execution Routine",
    lifespan=lifespan,
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal Server Error",
            "message": "An internal server error occurred.",
        },
    )
app.include_router(ambient.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(clipboard.router, prefix="/api/v1")
app.include_router(context_switch.router, prefix="/api/v1")
app.include_router(continuity.router, prefix="/api/v1/continuity", tags=["context-continuity"])
app.include_router(cognitive.router, prefix="/api/v1")
app.include_router(cache.router, prefix="/api/v1")
app.include_router(causal.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")
app.include_router(wake.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")
app.include_router(provenance.router, prefix="/api/v1")
app.include_router(privacy.router, prefix="/api/v1")
app.include_router(knowledge_graph.router, prefix="/api/v1")
app.include_router(reminders.router, prefix="/api/v1")
app.include_router(code_review.router, prefix="/api/v1")
app.include_router(vision.router, prefix="/api/v1")
app.include_router(guardian.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(meetings.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(episodes.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(email.router, prefix="/api/v1")
app.include_router(orchestration.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(self_memory.router, prefix="/api/v1")
app.include_router(self_improvement.router, prefix="/api/v1")
app.include_router(training.router, prefix="/api/v1")
app.include_router(federated.router, prefix="/api/v1")
app.include_router(routing_analytics.router, prefix="/api/v1")
app.include_router(workspace.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")
app.include_router(schedule.router, prefix="/api/v1")
app.include_router(schedule.events_router, prefix="/api/v1")
app.include_router(briefing.router, prefix="/api/v1")
app.include_router(images.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(skill_gaps.router, prefix="/api/v1")
app.include_router(telemetry_routes.router, prefix="/api/v1")
app.include_router(personality.router, prefix="/api/v1")
app.include_router(accountability.router, prefix="/api/v1")
app.include_router(plugins.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
app.include_router(catalog.router, prefix="/api/v1")
app.include_router(campaign_routes.router, prefix="/api")
app.include_router(campaign_routes.router, prefix="/api/v1")
app.include_router(campaign_routes.ws_router)
app.include_router(activation.router)
app.include_router(setup.router)

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
    return {
        "status": "healthy",
        "ollama": ollama_ok,
        "version": settings.APP_VERSION,
        "demo_mode": settings.COPPER_DEMO,
    }
