from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

db_url = getattr(settings, "DATABASE_URL", f"sqlite:///{settings.DB_PATH}")
engine_kwargs = {}
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30.0}
else:
    engine_kwargs["connect_args"] = {"connect_timeout": 3}
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 10
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(db_url, **engine_kwargs)

if db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
        except Exception:
            pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def close_db():
    """Disposes the SQLAlchemy engine connection pool and releases file handles."""
    try:
        engine.dispose()
    except Exception:
        pass


def init_db():
    if db_url.startswith("sqlite"):
        db_file = Path(settings.DB_PATH)
        db_file.parent.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)

    if db_url.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                from sqlalchemy import text

                res = conn.execute(text("PRAGMA table_info(response_evaluations)")).fetchall()
                col_names = {r[1] for r in res}
                if col_names and "model_name" not in col_names:
                    conn.execute(
                        text("ALTER TABLE response_evaluations ADD COLUMN model_name VARCHAR(100) DEFAULT 'default'")
                    )
                    conn.commit()
                if col_names and "latency_ms" not in col_names:
                    conn.execute(text("ALTER TABLE response_evaluations ADD COLUMN latency_ms FLOAT DEFAULT 0.0"))
                    conn.commit()
        except Exception:
            pass


import contextlib
import shutil
import time
from sqlalchemy import text


@contextlib.contextmanager
def resilient_transaction(db: Session):
    """Context manager for atomic transaction with rollback on failure."""
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


def execute_resilient_transaction(
    db: Session,
    operation: Callable[[Session], Any],
    max_retries: int = 3,
    base_delay_s: float = 0.1,
) -> Any:
    """Executes an operation within a resilient transaction, retrying on transient database lock errors."""
    from app.core.resilience.backoff import calculate_backoff

    for attempt in range(max_retries + 1):
        try:
            with resilient_transaction(db):
                return operation(db)
        except Exception as exc:
            err_msg = str(exc).lower()
            is_transient = any(phrase in err_msg for phrase in ["locked", "busy", "deadlock", "concurrent update"])
            if is_transient and attempt < max_retries:
                delay = calculate_backoff(attempt, base_delay_s=base_delay_s, max_delay_s=2.0)
                time.sleep(delay)
                continue
            raise


def check_db_health() -> dict[str, Any]:
    """Lightweight database connectivity probe."""
    from app.core.metrics import metrics_registry

    t0 = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        metrics_registry.record_database_health(True)
        return {"status": "healthy", "latency_ms": latency_ms, "db_type": "sqlite" if db_url.startswith("sqlite") else "postgres"}
    except Exception as exc:
        metrics_registry.record_database_health(False)
        return {"status": "degraded", "error": str(exc), "latency_ms": -1.0}


def checkpoint_wal(mode: str = "PASSIVE") -> dict[str, Any]:
    """Forces SQLite WAL checkpointing to truncate wal logs."""
    if not db_url.startswith("sqlite"):
        return {"status": "skipped", "reason": "Not an SQLite database"}

    valid_modes = {"PASSIVE", "FULL", "RESTART", "TRUNCATE"}
    chk_mode = mode.upper() if mode.upper() in valid_modes else "PASSIVE"

    try:
        with engine.connect() as conn:
            res = conn.execute(text(f"PRAGMA wal_checkpoint({chk_mode})")).fetchone()
            # res: (busy, log, checkpointed)
            return {
                "status": "success",
                "mode": chk_mode,
                "busy": res[0] if res else 0,
                "log_pages": res[1] if res else 0,
                "checkpointed_pages": res[2] if res else 0,
            }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def verify_and_backup_db(backup_dir: Path | None = None) -> dict[str, Any]:
    """Runs SQLite PRAGMA integrity_check and produces a verified timestamped backup copy."""
    if not db_url.startswith("sqlite"):
        return {"status": "skipped", "reason": "Not an SQLite database"}

    # 1. Integrity check
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("PRAGMA integrity_check")).fetchall()
            messages = [r[0] for r in rows]
            if messages != ["ok"]:
                return {"status": "corrupt", "details": messages}
    except Exception as exc:
        return {"status": "error", "error": f"Integrity check failed: {exc}"}

    # 2. Checkpoint WAL before copying
    checkpoint_wal("TRUNCATE")

    # 3. Create timestamped snapshot
    source_path = Path(settings.DB_PATH)
    if not source_path.exists():
        return {"status": "error", "error": f"Source DB {source_path} does not exist"}

    target_dir = backup_dir or (source_path.parent / "backups")
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_file = target_dir / f"copper_backup_{timestamp}.db"

    try:
        shutil.copy2(source_path, backup_file)
        return {
            "status": "success",
            "integrity": "ok",
            "backup_path": str(backup_file),
            "size_bytes": backup_file.stat().st_size,
        }
    except Exception as exc:
        return {"status": "error", "error": f"Backup copy failed: {exc}"}
