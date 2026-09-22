"""document metadata

Revision ID: 002
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("organization", sa.String(200), nullable=True))
    op.add_column(
        "projects",
        sa.Column("document_type", sa.String(100), nullable=False, server_default="Functional Documentation"),
    )
    op.add_column("projects", sa.Column("primary_users", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("how_to_read", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "how_to_read")
    op.drop_column("projects", "primary_users")
    op.drop_column("projects", "document_type")
    op.drop_column("projects", "organization")
