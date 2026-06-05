import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def get_fernet() -> Fernet:
    digest = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def mask_api_key(api_key: str) -> str:
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:3]}******{api_key[-4:]}"


def generate_secret_key() -> str:
    return Fernet.generate_key().decode("utf-8")


def encrypt_text(value: str) -> str:
    return get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_text(value: str) -> str:
    return get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
