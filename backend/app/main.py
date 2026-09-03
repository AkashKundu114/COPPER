from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.ai.llm.model_tier_manager import model_tier_manager
from app.ai.orchestration.task_scheduler import start_scheduler, stop_scheduler
from app.api.routes import (
    agents,
    audit,
    automation,
    chat,
    documents,
    episodes,
    guardian,
    knowledge_graph,
    memory,
    orchestration,
    reminders,
    self_improvement,
    self_memory,
    system,
    training,
    vision,
    voice,
    wake,
    workspace,
)
from app.core.config import settings
from app.core.logger import logger
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
    start_scheduler()
    model_tier_manager.start()
    logger.info("COPPER backend ready")
    yield
    await wake_word_service.disable()
    model_tier_manager.stop()
    stop_scheduler()
    await redis_close()
    logger.info("COPPER backend shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Centralized Omnifunctional Personal Productivity and Execution Routine",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.include_router(chat.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")
app.include_router(wake.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")
app.include_router(knowledge_graph.router, prefix="/api/v1")
app.include_router(reminders.router, prefix="/api/v1")
app.include_router(automation.router, prefix="/api/v1")
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
app.include_router(workspace.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "status": "online"}


@app.get("/health")
async def health():
    from app.ai.llm.ollama_client import ollama_client

    ollama_ok = await ollama_client.is_available()
    return {"status": "healthy", "ollama": ollama_ok, "version": settings.APP_VERSION}
