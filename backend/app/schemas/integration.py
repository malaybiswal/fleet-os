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


class DatConnectionTestResponse(BaseModel):
    success: bool
    message: str


class DatSyncResponse(BaseModel):
    fleets_processed: int
    fetched: int
    ingested: int
    skipped: int
