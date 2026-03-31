import hashlib
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock

from fastapi import Header, HTTPException, status

from db.models import AuthToken
from db import session as db_session


API_KEY_HEADER = "X-API-Key"
ADMIN_KEY_HEADER = "X-Admin-Key"


@dataclass
class TokenRecord:
    token: str
    source: str
    created_at: datetime
    expires_at: datetime | None
    note: str | None = None

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and datetime.now(UTC) >= self.expires_at

    def metadata(self) -> dict:
        suffix = self.token[-4:] if len(self.token) >= 4 else self.token
        return {
            "token_hint": f"***{suffix}",
            "source": self.source,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "is_expired": self.is_expired,
            "note": self.note,
        }


_token_lock = RLock()
_initialized = False
_env_tokens: set[str] = set()
_env_admin_tokens: set[str] = set()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _load_env_tokens() -> set[str]:
    tokens_csv = os.getenv("API_AUTH_TOKENS", "")
    tokens = {token.strip() for token in tokens_csv.split(",") if token.strip()}

    legacy_token = os.getenv("API_AUTH_TOKEN", "").strip()
    if legacy_token:
        tokens.add(legacy_token)

    return tokens


def _load_env_admin_tokens() -> set[str]:
    tokens_csv = os.getenv("API_ADMIN_TOKENS", "")
    tokens = {token.strip() for token in tokens_csv.split(",") if token.strip()}

    legacy_token = os.getenv("API_ADMIN_TOKEN", "").strip()
    if legacy_token:
        tokens.add(legacy_token)

    return tokens


def _initialize_tokens_if_needed() -> None:
    global _initialized, _env_tokens, _env_admin_tokens

    if _initialized:
        return

    with _token_lock:
        if _initialized:
            return

        _env_tokens = _load_env_tokens()
        _env_admin_tokens = _load_env_admin_tokens()

        db = db_session.SessionLocal()
        try:
            now = datetime.now(UTC)
            for token in _env_tokens:
                token_hash = _hash_token(token)
                existing = db.query(AuthToken).filter(AuthToken.token_hash == token_hash).first()
                if not existing:
                    db.add(
                        AuthToken(
                            token_hash=token_hash,
                            source="env",
                            created_at=now,
                            expires_at=None,
                            is_revoked=False,
                        )
                    )
            db.commit()
        finally:
            db.close()

        _initialized = True


def list_token_metadata() -> list[dict]:
    _initialize_tokens_if_needed()

    db = db_session.SessionLocal()
    try:
        now = datetime.now(UTC)
        records = (
            db.query(AuthToken)
            .filter(AuthToken.is_revoked == False)
            .filter((AuthToken.expires_at == None) | (AuthToken.expires_at > now))
            .order_by(AuthToken.source, AuthToken.created_at)
            .all()
        )

        metadata = []
        for record in records:
            token_hash = record.token_hash
            suffix = token_hash[-4:]
            metadata.append(
                {
                    "token_hint": f"***{suffix}",
                    "source": record.source,
                    "created_at": record.created_at,
                    "expires_at": record.expires_at,
                    "is_expired": record.expires_at is not None and record.expires_at <= now,
                    "note": record.note,
                }
            )
        return metadata
    finally:
        db.close()


def create_or_rotate_runtime_token(
    token: str | None,
    ttl_minutes: int | None,
    expires_at: datetime | None,
    note: str | None,
) -> tuple[str, dict]:
    _initialize_tokens_if_needed()

    if token is None:
        token = secrets.token_urlsafe(32)

    if ttl_minutes is not None and expires_at is not None:
        raise ValueError("Provide either ttl_minutes or expires_at, not both")

    computed_expiry = expires_at
    if ttl_minutes is not None:
        computed_expiry = datetime.now(UTC) + timedelta(minutes=ttl_minutes)

    db = db_session.SessionLocal()
    try:
        token_hash = _hash_token(token)
        now = datetime.now(UTC)

        db_record = AuthToken(
            token_hash=token_hash,
            source="runtime",
            created_at=now,
            expires_at=computed_expiry,
            note=note,
            is_revoked=False,
        )
        db.add(db_record)
        db.commit()

        record = TokenRecord(
            token=token,
            source="runtime",
            created_at=now,
            expires_at=computed_expiry,
            note=note,
        )
        return token, record.metadata()
    finally:
        db.close()


def revoke_runtime_token(token: str) -> bool:
    _initialize_tokens_if_needed()

    db = db_session.SessionLocal()
    try:
        token_hash = _hash_token(token)
        record = (
            db.query(AuthToken)
            .filter(AuthToken.token_hash == token_hash, AuthToken.source == "runtime")
            .first()
        )

        if record is None:
            return False

        record.is_revoked = True
        db.commit()
        return True
    finally:
        db.close()


def _is_valid_api_token(token: str) -> bool:
    _initialize_tokens_if_needed()

    token_hash = _hash_token(token)
    now = datetime.now(UTC)

    db = db_session.SessionLocal()
    try:
        record = (
            db.query(AuthToken)
            .filter(
                AuthToken.token_hash == token_hash,
                AuthToken.is_revoked == False,
            )
            .first()
        )

        if record is None:
            return False

        if record.expires_at is not None and record.expires_at <= now:
            return False

        return True
    finally:
        db.close()


def _is_valid_admin_token(token: str) -> bool:
    if token in _env_admin_tokens:
        return True

    if token in _env_tokens:
        return True

    return _is_valid_api_token(token)


def require_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    _initialize_tokens_if_needed()

    if not _env_admin_tokens and not _env_tokens:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No admin auth tokens are configured",
        )

    if not x_admin_key or not _is_valid_admin_token(x_admin_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
        )


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    _initialize_tokens_if_needed()

    if not _env_tokens:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No API auth tokens are configured",
        )

    if x_api_key in _env_tokens:
        return

    if not x_api_key or not _is_valid_api_token(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
