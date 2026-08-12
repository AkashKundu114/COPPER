"""add guardian, agent registry, and audit tables

Revision ID: 0002_guardian_agents_audit
Revises: 0001_initial
Create Date: 2026-08-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_guardian_agents_audit"
down_revision = "0001_initial"  # adjust to match your actual prior head revision
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_memories_v2",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, nullable=True, index=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("type", sa.Enum("fact", "observation", "hypothesis", name="memorytype"), nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("evidence_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.Enum("active", "superseded", "rejected", name="memorystatus"), nullable=False),
        sa.Column("supersedes_id", sa.Integer, nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "agent_versions",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("agent_id", sa.String(50), nullable=False, index=True),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("model_provider", sa.String(20), nullable=False, server_default="ollama"),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(20), nullable=True),
        sa.Column("tools", sa.JSON, nullable=True),
        sa.Column("capabilities", sa.JSON, nullable=True),
        sa.Column("status", sa.Enum("active", "candidate", "disabled", "rolled_back", name="agentstatus"), nullable=False),
        sa.Column("evaluation_score", sa.Float, nullable=True),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, nullable=True, index=True),
        sa.Column("session_id", sa.String(100), nullable=True, index=True),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("actor", sa.String(50), nullable=False),
        sa.Column("summary", sa.String(300), nullable=False),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("scope", sa.String(20), nullable=False, server_default="local"),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("audit_log")
    op.drop_table("agent_versions")
    op.drop_table("user_memories_v2")
    op.execute("DROP TYPE IF EXISTS memorytype")
    op.execute("DROP TYPE IF EXISTS memorystatus")
    op.execute("DROP TYPE IF EXISTS agentstatus")
