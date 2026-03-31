from imap_worker.worker import process_accounts_once
from db import session as db_session
from db.models import EmailMessage, IMAPAccount, Task


RAW_MESSAGE = b"""From: alerts@github.com\nTo: user@example.com\nSubject: TODO action required by 2030-01-01\nMessage-ID: <abc123@example.com>\nDate: Tue, 31 Mar 2026 10:00:00 +0000\n\nPlease action required and remind me tomorrow.\n"""


def test_worker_ingests_message_and_task(monkeypatch, configured_db):
    db = db_session.SessionLocal()
    try:
        account = IMAPAccount(host="imap.example.com", username="user@example.com", password="")
        account.set_password("top-secret")
        db.add(account)
        db.commit()
        db.refresh(account)
        account_id = account.id
    finally:
        db.close()

    class FakeClient:
        def __init__(self, account):
            self.account = account

        def fetch_new(self):
            return [(1, RAW_MESSAGE)]

    monkeypatch.setattr("imap_worker.worker.IMAPClient", FakeClient)

    process_accounts_once()
    process_accounts_once()

    db = db_session.SessionLocal()
    try:
        messages = db.query(EmailMessage).filter(EmailMessage.account_id == account_id).all()
        tasks = db.query(Task).all()
        account = db.query(IMAPAccount).filter(IMAPAccount.id == account_id).first()

        assert len(messages) == 1
        assert len(tasks) == 1
        assert messages[0].tags is not None
        assert account is not None
        assert account.last_uid == 1
    finally:
        db.close()
