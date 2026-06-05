from cryptography.fernet import Fernet


def mask_api_key(api_key: str) -> str:
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:3]}******{api_key[-4:]}"


def generate_secret_key() -> str:
    return Fernet.generate_key().decode("utf-8")
