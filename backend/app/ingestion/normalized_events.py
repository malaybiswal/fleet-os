from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class NormalizedEventType(StrEnum):
    TELEMETRY = "telemetry"
    LOAD = "load"


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


class NormalizedLoadObject(BaseModel):
    event_type: NormalizedEventType = NormalizedEventType.LOAD

    fleet_id: int
    source: str
    source_event_id: str

    origin: str
    destination: str
    origin_lat: float | None = None
    origin_lon: float | None = None
    equipment_type: str | None = None
    gross_revenue: float
    total_miles: float
    deadhead_miles: float = 0
    broker_name: str | None = None
    pickup_time: datetime | None = None
    delivery_time: datetime | None = None
    weight: float | None = None
    commodity: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
