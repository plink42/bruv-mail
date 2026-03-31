import json
import time

from imap_worker.imap_client import IMAPClient
from db.session import get_session
from imap_worker.parser import parse_email
from imap_worker.classifier import classify_email
from imap_worker.task_extractor import extract_tasks
from db.models import EmailMessage, IMAPAccount, Task

POLL_INTERVAL = 60  # seconds

def process_accounts_once() -> None:
    with get_session() as db:
        accounts = db.query(IMAPAccount).all()

        for account in accounts:
            client = IMAPClient(account)
            new_messages = client.fetch_new()
            max_uid_seen = account.last_uid or 0

            for uid, raw_msg in new_messages:
                parsed = parse_email(raw_msg)
                if not parsed.message_id:
                    continue

                existing = (
                    db.query(EmailMessage)
                    .filter(
                        EmailMessage.account_id == account.id,
                        EmailMessage.message_id == parsed.message_id,
                    )
                    .first()
                )
                if existing:
                    max_uid_seen = max(max_uid_seen, uid)
                    continue

                tags = classify_email(parsed)

                email = EmailMessage(
                    account_id=account.id,
                    message_id=parsed.message_id,
                    subject=parsed.subject,
                    from_addr=parsed.from_addr,
                    to_addrs=parsed.to_addrs,
                    date=parsed.date,
                    body_text=parsed.body_text,
                    body_html=parsed.body_html,
                    raw=raw_msg.decode("utf-8", errors="replace"),
                    tags=json.dumps(tags),
                )
                db.add(email)
                db.flush()

                extracted_tasks = extract_tasks(parsed)
                for task in extracted_tasks:
                    existing_task = (
                        db.query(Task)
                        .filter(Task.email_id == email.id, Task.title == task.title)
                        .first()
                    )
                    if existing_task:
                        continue

                    db.add(
                        Task(
                            email_id=email.id,
                            title=task.title,
                            due_date=task.due_date,
                            status="open",
                            confidence=task.confidence,
                        )
                    )

                max_uid_seen = max(max_uid_seen, uid)

            account.last_uid = max_uid_seen

        db.commit()


def run_worker():
    while True:
        process_accounts_once()

        time.sleep(POLL_INTERVAL)
