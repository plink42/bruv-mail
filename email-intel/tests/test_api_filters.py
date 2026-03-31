from datetime import UTC, datetime, timedelta

from db import session as db_session
from db.models import EmailMessage, Task


def test_messages_filter_and_pagination(client, seeded_account):
    db = db_session.SessionLocal()
    try:
        for idx in range(3):
            db.add(
                EmailMessage(
                    account_id=seeded_account.id,
                    message_id=f"msg-{idx}",
                    subject=f"Subject {idx}",
                    from_addr="sender@example.com" if idx < 2 else "other@example.com",
                    to_addrs="user@example.com",
                    date=datetime.now(UTC) - timedelta(days=idx),
                    body_text="hello",
                    body_html=None,
                    raw="raw",
                    tags='["finance"]' if idx == 0 else '["newsletter"]',
                )
            )
        db.commit()
    finally:
        db.close()

    resp = client.get(
        "/messages",
        params={"tag": "newsletter", "from_addr": "sender@", "limit": 1, "offset": 0},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["message_id"] == "msg-1"


def test_tasks_filter_and_status_patch(client, seeded_account):
    db = db_session.SessionLocal()
    try:
        email = EmailMessage(
            account_id=seeded_account.id,
            message_id="task-msg",
            subject="TODO: submit report",
            from_addr="boss@example.com",
            to_addrs="user@example.com",
            date=datetime.now(UTC),
            body_text="Please do this by 2030-01-01",
            body_html=None,
            raw="raw",
            tags='["work"]',
        )
        db.add(email)
        db.flush()

        task = Task(
            email_id=email.id,
            title="Submit report",
            due_date=datetime(2030, 1, 1),
            status="open",
            confidence=0.8,
        )
        db.add(task)
        db.commit()
        task_id = task.id
    finally:
        db.close()

    resp = client.get("/tasks", params={"status": "open"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 1

    patch_resp = client.patch(f"/tasks/{task_id}", json={"status": "done"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "done"
