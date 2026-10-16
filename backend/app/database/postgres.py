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
