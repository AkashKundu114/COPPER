"""Zero-Trust Security Policies and Dynamic Authorization Tables.

Revision ID: 0005_zero_trust_security_policies
Revises: 0004_productivity_tasks_projects_events
Create Date: 2026-11-10
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_zero_trust_security_policies"
down_revision = "0004_productivity_tasks_projects_events"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    tables = sa.inspect(bind).get_table_names()

    if "security_policies" not in tables:
        op.create_table(
            "security_policies",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False, unique=True),
            sa.Column("description", sa.String(255), nullable=True),
            sa.Column("policy_type", sa.String(50), nullable=False, server_default="rbac"),
            sa.Column("definition", sa.JSON, nullable=False),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )


def downgrade():
    bind = op.get_bind()
    tables = sa.inspect(bind).get_table_names()
    if "security_policies" in tables:
        op.drop_table("security_policies")
