import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from alembic.config import Config
from alembic import command
from sqlalchemy.orm import sessionmaker

from api import auth
from api.main import app
from db import session as db_session
from db.models import IMAPAccount


@pytest.fixture()
def db_file():
    fd, path = tempfile.mkstemp(prefix="email_intel_test_", suffix=".db")
    os.close(fd)
    try:
        yield path
    finally:
        if os.path.exists(path):
            os.remove(path)


@pytest.fixture()
def configured_db(db_file):
    db_url = f"sqlite:///{db_file}"
    os.environ["DATABASE_URL"] = db_url
    os.environ["APP_ENCRYPTION_KEY"] = "JfYf-yjvUN0p5XQH6Bbfazf2QmiVjCwXTlzAIXazhM4="
    os.environ["API_AUTH_TOKEN"] = "test-token"
    os.environ["API_AUTH_TOKENS"] = "test-token,rotated-token"
    os.environ["API_ADMIN_TOKEN"] = "admin-test-token"

    from sqlalchemy import create_engine as sa_create_engine
    
    # Reconfigure session for test database
    db_session.DATABASE_URL = db_url
    db_session.connect_args = {"check_same_thread": False}
    db_session.engine = sa_create_engine(db_url, connect_args=db_session.connect_args)
    db_session.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_session.engine)

    # Run Alembic migrations instead of create_all to match production
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    # Reset auth state for tests
    auth._initialized = False
    auth._env_tokens = set()
    auth._env_admin_tokens = set()

    yield

    # Reset auth state after test
    auth._initialized = False
    auth._env_tokens = set()
    auth._env_admin_tokens = set()


@pytest.fixture()
def client(configured_db):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def seeded_account(configured_db):
    db = db_session.SessionLocal()
    try:
        account = IMAPAccount(host="imap.example.com", username="user@example.com", password="", is_active=True)
        account.set_password("top-secret")
        db.add(account)
        db.commit()
        db.refresh(account)
        yield account
    finally:
        db.close()
