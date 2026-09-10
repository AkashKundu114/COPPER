import sqlalchemy as sa
from alembic import op

revision = "0004_productivity_tasks_projects_events"
down_revision = "0003_self_memory"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    tables = sa.inspect(bind).get_table_names()

    if "tasks" not in tables:
        op.create_table(
            "tasks",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("project", sa.String(100), nullable=False, server_default="General"),
            sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
            sa.Column("duration", sa.String(50), nullable=False, server_default="30m"),
            sa.Column("status", sa.String(20), nullable=False, server_default="inbox"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if "projects" not in tables:
        op.create_table(
            "projects",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("health", sa.String(20), nullable=False, server_default="healthy"),
            sa.Column("reason", sa.Text, nullable=True),
            sa.Column("completed_tasks", sa.Integer, nullable=False, server_default="0"),
            sa.Column("total_tasks", sa.Integer, nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if "schedule_events" not in tables:
        op.create_table(
            "schedule_events",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("time", sa.String(50), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("category", sa.String(50), nullable=False, server_default="Focus"),
            sa.Column("completed", sa.Boolean, nullable=False, server_default=sa.false()),
            sa.Column("date", sa.String(50), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )


def downgrade():
    op.drop_table("schedule_events")
    op.drop_table("projects")
    op.drop_table("tasks")
