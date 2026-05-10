from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TelemetryEventBase(BaseModel):
    truck_id: str
    timestamp: datetime
    speed: Decimal | None = None
    rpm: int | None = None
    engine_temp: Decimal | None = None
    fuel_level: Decimal | None = None
    gps_lat: Decimal | None = None
    gps_lon: Decimal | None = None
    idle_minutes: int | None = None
    reefer_temp: Decimal | None = None
    load_weight: Decimal | None = None


class TelemetryEventCreate(TelemetryEventBase):
    pass


class TelemetryEventResponse(TelemetryEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int