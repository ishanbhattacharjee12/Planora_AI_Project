"""project tech stack columns

Revision ID: 003
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("frontend_technology", sa.String(100), nullable=True))
    op.add_column("projects", sa.Column("backend_technology", sa.String(100), nullable=True))
    op.add_column("projects", sa.Column("database_technology", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "database_technology")
    op.drop_column("projects", "backend_technology")
    op.drop_column("projects", "frontend_technology")
