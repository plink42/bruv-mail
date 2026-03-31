import json
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth import (
    create_or_rotate_runtime_token,
    list_token_metadata,
    require_admin_key,
    require_api_key,
    revoke_runtime_token,
)
from db.models import EmailMessage, IMAPAccount, Task
from db.session import get_db

router = APIRouter()


class IMAPAccountCreate(BaseModel):
    host: str
    username: str
    password: str
    display_name: str | None = None


class IMAPAccountUpdate(BaseModel):
    display_name: str | None = None
    is_active: bool | None = None


class TaskStatusUpdate(BaseModel):
    status: Literal["open", "done", "dismissed"]


class TokenRotateRequest(BaseModel):
    token: str | None = None
    ttl_minutes: int | None = None
    expires_at: datetime | None = None
    note: str | None = None


class TokenRevokeRequest(BaseModel):
    token: str


def _parse_tags(raw_tags: str | None) -> list[str]:
    if not raw_tags:
        return []
    try:
        parsed = json.loads(raw_tags)
        if isinstance(parsed, list):
            return [str(tag) for tag in parsed]
    except json.JSONDecodeError:
        pass
    return [t.strip() for t in raw_tags.split(",") if t.strip()]


def _serialize_message(message: EmailMessage) -> dict:
    return {
        "id": message.id,
        "account_id": message.account_id,
        "message_id": message.message_id,
        "subject": message.subject,
        "from_addr": message.from_addr,
        "to_addrs": message.to_addrs,
        "date": message.date,
        "body_text": message.body_text,
        "body_html": message.body_html,
        "tags": _parse_tags(message.tags),
    }


def _serialize_task(task: Task) -> dict:
    return {
        "id": task.id,
        "email_id": task.email_id,
        "title": task.title,
        "due_date": task.due_date,
        "status": task.status,
        "confidence": task.confidence,
        "created_at": task.created_at,
    }


@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/messages")
def list_messages(
    tag: str | None = None,
    account_id: int | None = None,
    from_addr: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    q = db.query(EmailMessage)
    if tag:
        q = q.filter(EmailMessage.tags.contains(tag))
    if account_id is not None:
        q = q.filter(EmailMessage.account_id == account_id)
    if from_addr:
        q = q.filter(EmailMessage.from_addr.ilike(f"%{from_addr}%"))
    if date_from is not None:
        q = q.filter(EmailMessage.date >= date_from)
    if date_to is not None:
        q = q.filter(EmailMessage.date <= date_to)

    total = q.count()
    messages = q.order_by(EmailMessage.date.desc()).offset(offset).limit(limit).all()
    return {
        "items": [_serialize_message(msg) for msg in messages],
        "total": total,
        "limit": limit,
        "offset": offset,
    }

@router.get("/messages/{id}")
def get_message(id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    message = db.query(EmailMessage).filter(EmailMessage.id == id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return _serialize_message(message)

@router.get("/tags")
def list_tags(db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    counts: dict[str, int] = {}
    messages = db.query(EmailMessage.tags).all()
    for (raw_tags,) in messages:
        tags = _parse_tags(raw_tags)
        for tag in tags:
            counts[tag] = counts.get(tag, 0) + 1
    return [{"tag": k, "count": v} for k, v in sorted(counts.items(), key=lambda i: i[0])]

@router.post("/accounts")
def add_account(account: IMAPAccountCreate, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    existing = (
        db.query(IMAPAccount)
        .filter(IMAPAccount.host == account.host, IMAPAccount.username == account.username)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Account already exists")

    db_account = IMAPAccount(
        host=account.host,
        username=account.username,
        password="",
        display_name=account.display_name,
    )
    db_account.set_password(account.password)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return {
        "id": db_account.id,
        "host": db_account.host,
        "username": db_account.username,
        "display_name": db_account.display_name,
        "is_active": db_account.is_active,
        "last_uid": db_account.last_uid,
    }


@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    accounts = db.query(IMAPAccount).order_by(IMAPAccount.id.asc()).all()
    return [
        {
            "id": account.id,
            "host": account.host,
            "username": account.username,
            "display_name": account.display_name,
            "is_active": account.is_active,
            "last_uid": account.last_uid,
            "created_at": account.created_at,
        }
        for account in accounts
    ]


@router.patch("/accounts/{id}")
def update_account(
    id: int,
    payload: IMAPAccountUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    account = db.query(IMAPAccount).filter(IMAPAccount.id == id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if payload.display_name is not None:
        account.display_name = payload.display_name
    if payload.is_active is not None:
        account.is_active = payload.is_active

    db.commit()
    db.refresh(account)
    return {
        "id": account.id,
        "host": account.host,
        "username": account.username,
        "display_name": account.display_name,
        "is_active": account.is_active,
        "last_uid": account.last_uid,
        "created_at": account.created_at,
    }

@router.get("/tasks")
def list_tasks(
    status: Literal["open", "done", "dismissed"] | None = None,
    due_before: datetime | None = None,
    due_after: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    q = db.query(Task)
    if status is not None:
        q = q.filter(Task.status == status)
    if due_before is not None:
        q = q.filter(Task.due_date <= due_before)
    if due_after is not None:
        q = q.filter(Task.due_date >= due_after)

    total = q.count()
    tasks = q.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "items": [_serialize_task(task) for task in tasks],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.patch("/tasks/{id}")
def update_task_status(
    id: int,
    payload: TaskStatusUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    task = db.query(Task).filter(Task.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = payload.status
    db.commit()
    db.refresh(task)
    return _serialize_task(task)


@router.get("/auth/tokens")
def list_auth_tokens(_: None = Depends(require_admin_key)):
    return {"items": list_token_metadata()}


@router.post("/auth/tokens")
def rotate_auth_token(payload: TokenRotateRequest, _: None = Depends(require_admin_key)):
    try:
        token, metadata = create_or_rotate_runtime_token(
            token=payload.token,
            ttl_minutes=payload.ttl_minutes,
            expires_at=payload.expires_at,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "token": token,
        "metadata": metadata,
    }


@router.post("/auth/tokens/revoke")
def revoke_auth_token(payload: TokenRevokeRequest, _: None = Depends(require_admin_key)):
    revoked = revoke_runtime_token(payload.token)
    if not revoked:
        raise HTTPException(status_code=404, detail="Runtime token not found")
    return {"revoked": True}


app = FastAPI(title="email-intel")


app.include_router(router)
