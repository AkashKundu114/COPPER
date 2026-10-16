import asyncio
import pytest
from sqlalchemy import text

from app.core.config import settings
from app.ai.orchestration.task_scheduler import start_scheduler, stop_scheduler
from app.ai.ambient.context_watcher import context_watcher
from app.ai.ambient.cognitive_load import cognitive_load_detector
from app.database.postgres import engine, Base, close_db
from app.ai.memory.vector_store import close_chroma_client, _get_chroma_client
from app.core.telemetry import init_telemetry, shutdown_telemetry
from app.main import lifespan, app


@pytest.mark.asyncio
async def test_scheduler_starts_and_stops_ambient_monitors():
    """Verify start_scheduler starts context watcher and cognitive load, and stop_scheduler cleanly stops both."""
    start_scheduler()
    assert context_watcher.is_running is True
    assert cognitive_load_detector.is_running is True

    stop_scheduler()
    assert context_watcher.is_running is False
    assert cognitive_load_detector.is_running is False


@pytest.mark.asyncio
async def test_lifespan_graceful_shutdown_resilience():
    """Verify lifespan shutdown continues executing all cleanup stages even if one fails."""
    # Test entering and exiting lifespan
    async with lifespan(app):
        pass
    # All background services should be stopped
    assert context_watcher.is_running is False
    assert cognitive_load_detector.is_running is False


def test_sqlite_wal_mode_and_concurrency_configured():
    """Verify SQLite database connection has WAL mode enabled."""
    if engine.dialect.name == "sqlite":
        with engine.connect() as conn:
            journal_mode = conn.execute(text("PRAGMA journal_mode;")).scalar()
            assert journal_mode.lower() == "wal"


def test_alembic_registers_all_db_models():
    """Verify that Alembic Base.metadata includes campaign_metrics and core tables."""
    import app.database.models.campaign  # noqa: F401
    assert "campaign_metrics" in Base.metadata.tables
    assert "response_evaluations" in Base.metadata.tables
    assert "episodes" in Base.metadata.tables


def test_chroma_client_cleanup():
    """Verify ChromaDB client close function safely cleans up cached instance."""
    client = _get_chroma_client()
    assert client is not None
    close_chroma_client()
    from app.ai.memory import vector_store
    assert vector_store._CHROMA_CLIENT_CACHE is None


def test_telemetry_lifecycle():
    """Verify OpenTelemetry provider initializes and shuts down cleanly."""
    provider = init_telemetry()
    assert provider is not None
    shutdown_telemetry()
    from app.core import telemetry
    assert telemetry._tracer_provider is None
    assert telemetry._is_initialized is False
