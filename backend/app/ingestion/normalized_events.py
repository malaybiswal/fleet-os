from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class NormalizedEventType(StrEnum):
    TELEMETRY = "telemetry"


class NormalizedTelemetryEvent(BaseModel):
    event_type: NormalizedEventType = NormalizedEventType.TELEMETRY

    fleet_id: int
    truck_id: str

    timestamp: datetime

    latitude: float | None = None
    longitude: float | None = None
    speed_mph: float | None = None
    heading: int | None = None

    location_description: str | None = None
    status: str | None = None

    fuel_level: float | None = None
    engine_temp: float | None = None
    reefer_temp: float | None = None
    rpm: int | None = None

    source: str
    source_event_id: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
