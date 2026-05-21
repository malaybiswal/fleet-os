from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class LoadBase(BaseModel):
    load_id: str
    truck_id: str
    driver_id: str
    broker_name: str | None = None
    origin: str | None = None
    destination: str | None = None
    revenue: Decimal | None = None
    miles: Decimal | None = None
    deadhead_miles: Decimal | None = None
    fuel_cost: Decimal | None = None
    maintenance_reserve: Decimal | None = None
    driver_cost: Decimal | None = None
    tolls: Decimal | None = None
    pickup_time: datetime | None = None
    delivery_time: datetime | None = None
    status: str


class LoadCreate(LoadBase):
    pass


class LoadUpdate(BaseModel):
    truck_id: str | None = None
    driver_id: str | None = None
    broker_name: str | None = None
    origin: str | None = None
    destination: str | None = None
    revenue: Decimal | None = None
    miles: Decimal | None = None
    deadhead_miles: Decimal | None = None
    fuel_cost: Decimal | None = None
    maintenance_reserve: Decimal | None = None
    driver_cost: Decimal | None = None
    tolls: Decimal | None = None
    pickup_time: datetime | None = None
    delivery_time: datetime | None = None
    status: str | None = None


class LoadResponse(LoadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fleet_id: int | None = None


class LoadProfitability(BaseModel):
    load_id: str
    revenue: Decimal | None = None
    miles: Decimal | None = None
    deadhead_miles: Decimal | None = None
    revenue_per_mile: Decimal | None = None
    deadhead_percentage: Decimal | None = None
    net_profit: Decimal | None = None
