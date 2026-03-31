"""add account metadata

Revision ID: 0002_account_metadata
Revises: 0001_initial_schema
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_account_metadata"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("imap_accounts", sa.Column("display_name", sa.String(), nullable=True))
    op.add_column(
        "imap_accounts",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "imap_accounts",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_column("imap_accounts", "created_at")
    op.drop_column("imap_accounts", "is_active")
    op.drop_column("imap_accounts", "display_name")
