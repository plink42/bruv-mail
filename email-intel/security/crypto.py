import os

from cryptography.fernet import Fernet


def _get_key() -> bytes:
    configured = os.getenv("APP_ENCRYPTION_KEY")
    if not configured:
        raise RuntimeError("APP_ENCRYPTION_KEY is required")
    return configured.encode("utf-8")


def _get_fernet() -> Fernet:
    key = _get_key()
    try:
        return Fernet(key)
    except Exception as exc:
        raise RuntimeError("APP_ENCRYPTION_KEY is invalid") from exc


def encrypt_secret(value: str) -> str:
    token = _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")
    return f"enc:v1:{token}"


def decrypt_secret(value: str) -> str:
    if value.startswith("enc:v1:"):
        token = value[len("enc:v1:") :]
        return _get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    return value
