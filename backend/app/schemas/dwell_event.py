from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DwellEventBase(BaseModel):
    load_id: str
    facility_name: str | None = None
    broker_name: str | None = None
    appointment_time: datetime | None = None
    arrival_time: datetime | None = None
    loading_start: datetime | None = None
    loading_end: datetime | None = None
    departure_time: datetime | None = None
    detention_pay: Decimal | None = None
    driver_notes: str | None = None


class DwellEventCreate(DwellEventBase):
    pass


class DwellEventUpdate(BaseModel):
    facility_name: str | None = None
    broker_name: str | None = None
    appointment_time: datetime | None = None
    arrival_time: datetime | None = None
    loading_start: datetime | None = None
    loading_end: datetime | None = None
    departure_time: datetime | None = None
    detention_pay: Decimal | None = None
    driver_notes: str | None = None


class DwellEventResponse(DwellEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fleet_id: int | None = None
    facility_id: int | None = None


class FacilityScorecard(BaseModel):
    facility_name: str
    avg_dwell_hours: float
    avg_loading_delay_hours: float
    total_detention_pay: Decimal
    visit_count: int
    facility_score: float


class BrokerScorecard(BaseModel):
    broker_name: str
    avg_dwell_hours: float
    avg_loading_delay_hours: float
    total_detention_pay: Decimal
    load_count: int
