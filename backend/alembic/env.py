import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Ensure backend root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.postgres import Base, db_url  # noqa: E402
import app.database.models.agent_registry  # noqa: F401, E402
import app.database.models.audit_log  # noqa: F401, E402
import app.database.models.episode  # noqa: F401, E402
import app.database.models.history  # noqa: F401, E402
import app.database.models.knowledge_graph  # noqa: F401, E402
import app.database.models.lora_adapter  # noqa: F401, E402
import app.database.models.memory_v2  # noqa: F401, E402
import app.database.models.project  # noqa: F401, E402
import app.database.models.response_evaluation  # noqa: F401, E402
import app.database.models.schedule_event  # noqa: F401, E402
import app.database.models.self_memory  # noqa: F401, E402
import app.database.models.task  # noqa: F401, E402
import app.database.models.workspace  # noqa: F401, E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

is_sqlite = db_url.startswith("sqlite")


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=is_sqlite,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = db_url
    connect_args = {"check_same_thread": False} if is_sqlite else {}

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=is_sqlite,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
