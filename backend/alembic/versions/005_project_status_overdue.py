"""add overdue to project status enum

Revision ID: 005
"""

from alembic import op
import sqlalchemy as sa


revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'overdue'")


def downgrade() -> None:
    pass
