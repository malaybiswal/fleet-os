from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


class CredentialEncryptionConfigError(RuntimeError):
    pass


class CredentialDecryptionError(RuntimeError):
    pass


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise CredentialDecryptionError("Stored credentials could not be decrypted") from exc


def _fernet() -> Fernet:
    key = settings.CREDENTIAL_ENCRYPTION_KEY
    if not key:
        raise CredentialEncryptionConfigError(
            "CREDENTIAL_ENCRYPTION_KEY is required for integration credentials"
        )
    try:
        return Fernet(key.encode("utf-8"))
    except ValueError as exc:
        raise CredentialEncryptionConfigError(
            "CREDENTIAL_ENCRYPTION_KEY must be a valid Fernet key"
        ) from exc
