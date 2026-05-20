from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class CarrierBase(BaseModel):
    dot_number: str
    mc_number: str | None = None
    legal_name: str
    dba_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address_line1: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    authority_status: str | None = None
    authority_date: date | None = None
    power_units: int | None = None
    driver_count: int | None = None
    cargo_types: list[str] | None = None
    outreach_status: str = "not_contacted"


class CarrierCreate(CarrierBase):
    pass


class CarrierListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dot_number: str
    mc_number: str | None = None
    legal_name: str
    dba_name: str | None = None
    state: str | None = None
    authority_status: str | None = None
    authority_date: date | None = None
    power_units: int | None = None
    driver_count: int | None = None
    outreach_status: str


class CarrierRead(CarrierBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class CarrierSnapshotBase(BaseModel):
    carrier_id: int
    snapshot_date: date
    power_units: int | None = None
    driver_count: int | None = None
    authority_status: str | None = None
    cargo_types: list[str] | None = None
    raw_payload: dict | None = None


class CarrierSnapshotCreate(CarrierSnapshotBase):
    pass


class CarrierSnapshotRead(CarrierSnapshotBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class OutreachNoteBase(BaseModel):
    carrier_id: int
    note: str
    outcome: str | None = None
    follow_up_date: datetime | None = None
    contact_name: str | None = None
    dispatcher_name: str | None = None
    pain_points: str | None = None
    created_by: str | None = None


class OutreachNoteCreate(OutreachNoteBase):
    pass


class OutreachNoteRead(OutreachNoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class TagBase(BaseModel):
    name: str
    display_name: str | None = None


class TagCreate(TagBase):
    pass


class TagRead(TagBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
