import sqlalchemy as sa
from alembic import op

revision = "0003_self_memory"
down_revision = "0002_guardian_agents_audit"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "self_memory",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("category", sa.Enum("decision", "correction", "position", "track_record", "open_question", name="selfmemorycategory"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("outcome", sa.Enum("confirmed_helpful", "confirmed_wrong", "unknown", name="selfmemoryoutcome"), nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("evidence_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("related_episode_id", sa.Integer, nullable=True),
        sa.Column("superseded_by", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_reinforced_at", sa.DateTime(timezone=True), nullable=True),
    )

def downgrade():
    op.drop_table("self_memory")
    op.execute("DROP TYPE IF EXISTS selfmemorycategory")
    op.execute("DROP TYPE IF EXISTS selfmemoryoutcome")
