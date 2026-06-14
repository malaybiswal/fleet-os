from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LivePositionAlert(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    severity: str
    alert_type: str
    message: str | None
    created_at: datetime


class LiveTruckPosition(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    truck_id: str
    status: str
    latitude: float | None
    longitude: float | None
    speed: float | None
    heading: int | None
    last_seen_at: datetime | None
    current_location: str | None
    active_alert_count: int = 0
    highest_alert_severity: str | None = None
    active_alerts: list[LivePositionAlert] = Field(default_factory=list)
