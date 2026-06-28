import pytest
from cryptography.fernet import Fernet

from app.config import settings
from app.core.crypto import CredentialEncryptionConfigError, decrypt, encrypt


def test_encrypt_decrypt_round_trip(monkeypatch):
    monkeypatch.setattr(settings, "CREDENTIAL_ENCRYPTION_KEY", Fernet.generate_key().decode())

    token = encrypt("secret-json")

    assert token != "secret-json"
    assert decrypt(token) == "secret-json"


def test_encrypt_requires_configured_key(monkeypatch):
    monkeypatch.setattr(settings, "CREDENTIAL_ENCRYPTION_KEY", None)

    with pytest.raises(CredentialEncryptionConfigError):
        encrypt("secret-json")
