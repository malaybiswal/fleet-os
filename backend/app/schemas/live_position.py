from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LiveTruckPosition(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    truck_id: str
    status: str
    latitude: float | None
    longitude: float | None
    speed: float | None
    last_seen_at: datetime | None
    current_location: str | None
