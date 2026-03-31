"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "imap_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("host", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("last_uid", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("host", "username", name="uq_imap_accounts_host_username"),
    )

    op.create_table(
        "email_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("from_addr", sa.String(), nullable=True),
        sa.Column("to_addrs", sa.Text(), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("raw", sa.Text(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["imap_accounts.id"]),
        sa.UniqueConstraint("account_id", "message_id", name="uq_email_messages_account_message_id"),
    )
    op.create_index("ix_email_messages_date", "email_messages", ["date"])
    op.create_index("ix_email_messages_from_addr", "email_messages", ["from_addr"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["email_id"], ["email_messages.id"]),
        sa.UniqueConstraint("email_id", "title", name="uq_tasks_email_title"),
    )
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_due_date", "tasks", ["due_date"])


def downgrade() -> None:
    op.drop_index("ix_tasks_due_date", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_table("tasks")

    op.drop_index("ix_email_messages_from_addr", table_name="email_messages")
    op.drop_index("ix_email_messages_date", table_name="email_messages")
    op.drop_table("email_messages")

    op.drop_table("imap_accounts")
