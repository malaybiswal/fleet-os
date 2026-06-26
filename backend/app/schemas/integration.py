from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DatCredentialRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    base_url: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    provider_mode: str | None = None


class DatIntegrationStatus(BaseModel):
    connected: bool
    status: str
    last_sync_at: datetime | None = None
    last_error: str | None = None
    # Non-secret saved config so the UI can reflect a connected integration.
    # The password is never surfaced.
    username: str | None = None
    base_url: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)


class DatConnectionTestResponse(BaseModel):
    success: bool
    message: str


class DatSyncAccepted(BaseModel):
    status: str = "accepted"
    detail: str
