from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TruckBase(BaseModel):
    truck_id: str
    status: str
    current_location: str | None = None
    current_lat: Decimal | None = None
    current_lon: Decimal | None = None
    last_seen_at: datetime | None = None


class TruckCreate(TruckBase):
    pass


class TruckUpdate(BaseModel):
    status: str | None = None
    current_location: str | None = None
    current_lat: Decimal | None = None
    current_lon: Decimal | None = None
    last_seen_at: datetime | None = None


class TruckResponse(TruckBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fleet_id: int | None = None
    created_at: datetime
