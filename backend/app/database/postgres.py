from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

db_url = getattr(settings, "DATABASE_URL", f"sqlite:///{settings.DB_PATH}")
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    if db_url.startswith("sqlite"):
        db_file = Path(settings.DB_PATH)
        db_file.parent.mkdir(parents=True, exist_ok=True)
    import app.database.models.agent_registry  # noqa: F401
    import app.database.models.audit_log  # noqa: F401
    import app.database.models.episode  # noqa: F401
    import app.database.models.history  # noqa: F401
    import app.database.models.knowledge_graph  # noqa: F401
    import app.database.models.lora_adapter  # noqa: F401
    import app.database.models.memory_v2  # noqa: F401
    import app.database.models.response_evaluation  # noqa: F401
    import app.database.models.self_memory  # noqa: F401
    import app.database.models.workspace  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Lightweight schema migration for SQLite
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
