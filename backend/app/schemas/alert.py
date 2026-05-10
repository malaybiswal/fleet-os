from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertBase(BaseModel):
    truck_id: str
    severity: str
    alert_type: str
    message: str | None = None
    resolved: bool = False


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    resolved: bool | None = None


class AlertResponse(AlertBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime