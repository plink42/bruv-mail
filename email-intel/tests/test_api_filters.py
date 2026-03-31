from datetime import UTC, datetime, timedelta

import pytest

from db import session as db_session
from db.models import EmailMessage, Task

AUTH_HEADERS = {"X-API-Key": "test-token"}
ROTATED_AUTH_HEADERS = {"X-API-Key": "rotated-token"}
ADMIN_HEADERS = {"X-Admin-Key": "test-token"}


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
        headers=AUTH_HEADERS,
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

    resp = client.get("/tasks", params={"status": "open"}, headers=AUTH_HEADERS)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 1

    patch_resp = client.patch(f"/tasks/{task_id}", json={"status": "done"}, headers=AUTH_HEADERS)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "done"


def test_token_rotation_support(client):
    resp = client.get("/messages", headers=ROTATED_AUTH_HEADERS)
    assert resp.status_code == 200


def test_update_account(client, seeded_account):
    resp = client.patch(
        f"/accounts/{seeded_account.id}",
        json={"display_name": "Primary Inbox", "is_active": False},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["display_name"] == "Primary Inbox"
    assert payload["is_active"] is False


def test_runtime_token_rotation_and_revoke(client):
    create_resp = client.post(
        "/auth/tokens",
        json={"ttl_minutes": 10, "note": "deploy-window"},
        headers=ADMIN_HEADERS,
    )
    assert create_resp.status_code == 200
    token = create_resp.json()["token"]
    assert token

    use_resp = client.get("/messages", headers={"X-API-Key": token})
    assert use_resp.status_code == 200

    revoke_resp = client.post(
        "/auth/tokens/revoke",
        json={"token": token},
        headers=ADMIN_HEADERS,
    )
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["revoked"] is True

    after_revoke_resp = client.get("/messages", headers={"X-API-Key": token})
    assert after_revoke_resp.status_code == 401


def test_expired_runtime_token_rejected(client):
    create_resp = client.post(
        "/auth/tokens",
        json={"ttl_minutes": 0, "note": "immediate-expiry"},
        headers=ADMIN_HEADERS,
    )
    assert create_resp.status_code == 200
    token = create_resp.json()["token"]

    use_resp = client.get("/messages", headers={"X-API-Key": token})
    assert use_resp.status_code == 401


def test_admin_key_required_for_auth_endpoints(client):
    list_resp = client.get("/auth/tokens")
    assert list_resp.status_code == 401

    create_resp = client.post("/auth/tokens", json={"ttl_minutes": 5})
    assert create_resp.status_code == 401

    revoke_resp = client.post("/auth/tokens/revoke", json={"token": "anything"})
    assert revoke_resp.status_code == 401


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/messages", None),
        ("get", "/messages/1", None),
        ("get", "/tags", None),
        ("post", "/accounts", {"host": "imap.example.com", "username": "new@example.com", "password": "pw"}),
        ("get", "/accounts", None),
        ("patch", "/accounts/1", {"display_name": "x", "is_active": True}),
        ("get", "/tasks", None),
        ("patch", "/tasks/1", {"status": "done"}),
    ],
)
def test_auth_required(client, method, path, payload):
    request = getattr(client, method)
    kwargs = {}
    if payload is not None:
        kwargs["json"] = payload

    resp = request(path, **kwargs)
    assert resp.status_code == 401
