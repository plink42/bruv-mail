# db/models.py

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.session import Base
from security.crypto import decrypt_secret, encrypt_secret

class IMAPAccount(Base):
    __tablename__ = "imap_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    host: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    last_uid: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("host", "username", name="uq_imap_accounts_host_username"),
    )

    def set_password(self, plain_password: str) -> None:
        self.password = encrypt_secret(plain_password)

    def get_password(self) -> str:
        return decrypt_secret(self.password)

class EmailMessage(Base):
    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("imap_accounts.id"), nullable=False)
    message_id: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str | None] = mapped_column(String)
    from_addr: Mapped[str | None] = mapped_column(String)
    to_addrs: Mapped[str | None] = mapped_column(Text)
    date: Mapped[datetime | None] = mapped_column(DateTime)
    body_text: Mapped[str | None] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text)
    raw: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[str | None] = mapped_column(Text)  # JSON list or comma-separated

    __table_args__ = (
        UniqueConstraint("account_id", "message_id", name="uq_email_messages_account_message_id"),
        Index("ix_email_messages_date", "date"),
        Index("ix_email_messages_from_addr", "from_addr"),
    )

    account: Mapped[IMAPAccount] = relationship("IMAPAccount")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="email", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("email_messages.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_due_date", "due_date"),
        UniqueConstraint("email_id", "title", name="uq_tasks_email_title"),
    )

    email: Mapped[EmailMessage] = relationship("EmailMessage", back_populates="tasks")
