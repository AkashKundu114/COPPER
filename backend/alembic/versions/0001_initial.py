import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    tables = sa.inspect(bind).get_table_names()

    if "chat_history" not in tables:
        op.create_table(
            "chat_history",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("session_id", sa.String(64), nullable=False, index=True),
            sa.Column("sender", sa.String(16), nullable=False),
            sa.Column("message", sa.Text, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if "workspace_items" not in tables:
        op.create_table(
            "workspace_items",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("kind", sa.String(32), nullable=False, index=True),
            sa.Column("payload", sa.JSON, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if "episodes" not in tables:
        op.create_table(
            "episodes",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("session_id", sa.String(100), nullable=False, index=True),
            sa.Column("user_query", sa.Text, nullable=False),
            sa.Column("agent_response", sa.Text, nullable=False),
            sa.Column("turn_count", sa.Integer, default=1),
            sa.Column("duration_ms", sa.Float, default=0.0),
            sa.Column("metadata", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if "response_evaluations" not in tables:
        op.create_table(
            "response_evaluations",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("user_query", sa.Text, nullable=False),
            sa.Column("response", sa.Text, nullable=False),
            sa.Column("domain", sa.String(50), nullable=False, server_default="general"),
            sa.Column("model_name", sa.String(100), nullable=False, server_default="default"),
            sa.Column("overall_score", sa.Float, nullable=False),
            sa.Column("fluency", sa.Float, default=0.0),
            sa.Column("accuracy", sa.Float, default=0.0),
            sa.Column("completeness", sa.Float, default=0.0),
            sa.Column("conciseness", sa.Float, default=0.0),
            sa.Column("latency_ms", sa.Float, default=0.0),
            sa.Column("flagged_issue", sa.String(100), nullable=True),
            sa.Column("detailed_feedback", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if "lora_adapters" not in tables:
        op.create_table(
            "lora_adapters",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("name", sa.String(100), nullable=False, unique=True),
            sa.Column("base_model", sa.String(100), nullable=False),
            sa.Column("description", sa.String(255), nullable=True),
            sa.Column("version", sa.String(20), nullable=False, server_default="1.0.0"),
            sa.Column("weights_path", sa.String(255), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="ready"),
            sa.Column("performance_score", sa.Float, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if "knowledge_entities" not in tables:
        op.create_table(
            "knowledge_entities",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("name", sa.String(150), nullable=False, index=True),
            sa.Column("canonical_name", sa.String(150), nullable=False, index=True),
            sa.Column("type", sa.String(50), nullable=False, index=True),
            sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
            sa.Column("context", sa.Text, nullable=True),
            sa.Column("evidence_count", sa.Integer, nullable=False, server_default="1"),
            sa.Column("extra_metadata", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if "knowledge_relationships" not in tables:
        op.create_table(
            "knowledge_relationships",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("source_id", sa.Integer, sa.ForeignKey("knowledge_entities.id", ondelete="CASCADE"), nullable=True, index=True),
            sa.Column("target_id", sa.Integer, sa.ForeignKey("knowledge_entities.id", ondelete="CASCADE"), nullable=True, index=True),
            sa.Column("source", sa.String(150), nullable=False, index=True),
            sa.Column("target", sa.String(150), nullable=False, index=True),
            sa.Column("type", sa.String(50), nullable=False, index=True),
            sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
            sa.Column("context", sa.Text, nullable=True),
            sa.Column("evidence_count", sa.Integer, nullable=False, server_default="1"),
            sa.Column("extra_metadata", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )


def downgrade():
    op.drop_table("knowledge_relationships")
    op.drop_table("knowledge_entities")
    op.drop_table("lora_adapters")
    op.drop_table("response_evaluations")
    op.drop_table("episodes")
    op.drop_table("workspace_items")
    op.drop_table("chat_history")
