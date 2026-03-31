import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock

from fastapi import Header, HTTPException, status


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
_runtime_tokens: dict[str, TokenRecord] = {}


def _load_valid_tokens() -> set[str]:
    tokens_csv = os.getenv("API_AUTH_TOKENS", "")
    tokens = {token.strip() for token in tokens_csv.split(",") if token.strip()}

    # Backward-compatible single-token support.
    legacy_token = os.getenv("API_AUTH_TOKEN", "").strip()
    if legacy_token:
        tokens.add(legacy_token)

    return tokens


def _load_admin_tokens() -> set[str]:
    tokens_csv = os.getenv("API_ADMIN_TOKENS", "")
    tokens = {token.strip() for token in tokens_csv.split(",") if token.strip()}

    legacy_token = os.getenv("API_ADMIN_TOKEN", "").strip()
    if legacy_token:
        tokens.add(legacy_token)

    return tokens


def _initialize_tokens_if_needed() -> None:
    global _initialized
    if _initialized:
        return

    with _token_lock:
        if _initialized:
            return

        now = datetime.now(UTC)
        for token in _load_valid_tokens():
            _runtime_tokens[token] = TokenRecord(
                token=token,
                source="env",
                created_at=now,
                expires_at=None,
            )

        _initialized = True


def _purge_expired_tokens() -> None:
    expired = [token for token, record in _runtime_tokens.items() if record.is_expired]
    for token in expired:
        del _runtime_tokens[token]


def list_token_metadata() -> list[dict]:
    _initialize_tokens_if_needed()
    with _token_lock:
        _purge_expired_tokens()
        metadata = [record.metadata() for record in _runtime_tokens.values()]
    return sorted(metadata, key=lambda row: (row["source"], row["token_hint"]))


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

    now = datetime.now(UTC)
    with _token_lock:
        _runtime_tokens[token] = TokenRecord(
            token=token,
            source="runtime",
            created_at=now,
            expires_at=computed_expiry,
            note=note,
        )
        record = _runtime_tokens[token]
    return token, record.metadata()


def revoke_runtime_token(token: str) -> bool:
    _initialize_tokens_if_needed()
    with _token_lock:
        record = _runtime_tokens.get(token)
        if record is None or record.source != "runtime":
            return False
        del _runtime_tokens[token]
        return True


def require_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    valid_admin_tokens = _load_admin_tokens()
    if not valid_admin_tokens:
        valid_admin_tokens = _load_valid_tokens()

    if not valid_admin_tokens:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No admin auth tokens are configured",
        )

    if not x_admin_key or x_admin_key not in valid_admin_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
        )


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    _initialize_tokens_if_needed()
    with _token_lock:
        _purge_expired_tokens()
        valid_tokens = set(_runtime_tokens.keys())

    if not valid_tokens:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No API auth tokens are configured",
        )

    if not x_api_key or x_api_key not in valid_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
