import base64
import hashlib
import os

from cryptography.fernet import Fernet


def _derive_dev_key() -> bytes:
    digest = hashlib.sha256(b"email-intel-dev-key-change-me").digest()
    return base64.urlsafe_b64encode(digest)


def _get_key() -> bytes:
    configured = os.getenv("APP_ENCRYPTION_KEY")
    if configured:
        return configured.encode("utf-8")
    return _derive_dev_key()


def _get_fernet() -> Fernet:
    return Fernet(_get_key())


def encrypt_secret(value: str) -> str:
    token = _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")
    return f"enc:v1:{token}"


def decrypt_secret(value: str) -> str:
    if value.startswith("enc:v1:"):
        token = value[len("enc:v1:") :]
        return _get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    return value
