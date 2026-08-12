from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Determine database URL (defaults to local SQLite)
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
    # Ensure data directory exists for SQLite
    if db_url.startswith("sqlite"):
        db_file = Path(settings.DB_PATH)
        db_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create all tables defined in models
    import app.database.models.agent_registry  # noqa: F401
    import app.database.models.audit_log      # noqa: F401
    import app.database.models.memory_v2     # noqa: F401
    
    Base.metadata.create_all(bind=engine)
