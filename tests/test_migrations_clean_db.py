import gc
import tempfile
from pathlib import Path
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, inspect

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

def test_alembic_migrations_clean_database():
    """
    Verifies that Alembic migrations run cleanly from scratch
    on a completely empty SQLite database up to 'head' and create
    all required schema tables.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db_path = Path(tmp_dir) / "clean_migration_test.db"
        db_url = f"sqlite:///{test_db_path.as_posix()}"

        alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)

        # 1. Upgrade from clean base to head
        command.upgrade(alembic_cfg, "head")
        assert test_db_path.exists(), "Migration did not generate SQLite database file."

        # 2. Inspect created tables
        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        expected_core_tables = {
            "alembic_version",
            "agent_versions",
            "audit_log",
            "chat_history",
            "episodes",
            "knowledge_entities",
            "knowledge_relationships",
            "lora_adapters",
            "projects",
            "response_evaluations",
            "schedule_events",
            "self_memory",
            "tasks",
            "user_memories_v2",
            "workspace_items",
        }

        for tbl in expected_core_tables:
            assert tbl in tables, f"Expected table '{tbl}' not found in migrated database schema."

        engine.dispose()
        del engine
        gc.collect()
