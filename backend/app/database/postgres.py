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
    Base.metadata.create_all(bind=engine)
