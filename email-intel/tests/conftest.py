import os
import tempfile

import pytest
from fastapi.testclient import TestClient

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
    db_session.DATABASE_URL = db_url
    db_session.connect_args = {"check_same_thread": False}
    db_session.engine = db_session.create_engine(db_url, connect_args=db_session.connect_args)
    db_session.SessionLocal.configure(bind=db_session.engine)
    db_session.Base.metadata.create_all(bind=db_session.engine)

    yield


@pytest.fixture()
def client(configured_db):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def seeded_account(configured_db):
    db = db_session.SessionLocal()
    try:
        account = IMAPAccount(host="imap.example.com", username="user@example.com", password="")
        account.set_password("top-secret")
        db.add(account)
        db.commit()
        db.refresh(account)
        yield account
    finally:
        db.close()
