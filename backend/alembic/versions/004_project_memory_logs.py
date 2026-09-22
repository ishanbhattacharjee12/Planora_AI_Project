"""project semantic memory logs

Revision ID: 004
"""

from alembic import op
import sqlalchemy as sa


revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_memory_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("snippet", sa.String(320), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("architecture", sa.Text(), nullable=False),
        sa.Column("semantic_summary", sa.Text(), nullable=False),
        sa.Column("chroma_id", sa.String(100), nullable=False),
        sa.Column("index_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("index_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id"),
        sa.UniqueConstraint("chroma_id"),
    )
    op.create_index("ix_project_memory_logs_project_id", "project_memory_logs", ["project_id"])
    op.create_index("ix_project_memory_logs_owner_id", "project_memory_logs", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_project_memory_logs_owner_id", table_name="project_memory_logs")
    op.drop_index("ix_project_memory_logs_project_id", table_name="project_memory_logs")
    op.drop_table("project_memory_logs")
