import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def enable_dev_auth_for_tests(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", True)
