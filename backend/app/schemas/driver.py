from pydantic import BaseModel, ConfigDict


class DriverBase(BaseModel):
    driver_id: str
    name: str
    status: str


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    name: str | None = None
    status: str | None = None


class DriverResponse(DriverBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fleet_id: int | None = None
    hos_hours_remaining: float | None = None
