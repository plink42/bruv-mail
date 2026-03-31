"""add auth_tokens table for persistent token storage

Revision ID: 0003_auth_tokens
Revises: 0002_account_metadata
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_auth_tokens"
down_revision = "0002_account_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_auth_tokens_token_hash"),
    )
    op.create_index("ix_auth_tokens_token_hash", "auth_tokens", ["token_hash"])
    op.create_index("ix_auth_tokens_expires_at", "auth_tokens", ["expires_at"])
    op.create_index("ix_auth_tokens_is_revoked", "auth_tokens", ["is_revoked"])


def downgrade() -> None:
    op.drop_table("auth_tokens")
