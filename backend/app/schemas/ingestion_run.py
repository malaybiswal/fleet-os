from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IngestionRunCreate(BaseModel):
    provider: str
    entity_type: str
    status: str
    started_at: datetime
    cursor_from: datetime | None = None


class IngestionRunUpdate(BaseModel):
    status: str | None = None
    completed_at: datetime | None = None
    records_fetched: int | None = None
    records_upserted: int | None = None
    cursor_to: datetime | None = None
    error_message: str | None = None


class IngestionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    entity_type: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    records_fetched: int | None = None
    records_upserted: int | None = None
    cursor_from: datetime | None = None
    cursor_to: datetime | None = None
    error_message: str | None = None
