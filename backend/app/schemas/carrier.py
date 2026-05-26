from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field

from app.models.carrier import OutreachStatus


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    total: int
    page: int
    page_size: int

    @computed_field
    @property
    def total_pages(self) -> int:
        if self.total == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @computed_field
    @property
    def has_previous(self) -> bool:
        return self.page > 1 and self.total > 0


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
    lead_score: int | None = None
    outreach_status: str
    created_at: datetime
    updated_at: datetime


class CarrierRead(CarrierBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_score: int | None = None
    created_at: datetime
    updated_at: datetime


class CarrierSnapshotBase(BaseModel):
    carrier_id: int
    snapshot_date: date
    power_units: int | None = None
    driver_count: int | None = None
    authority_status: str | None = None
    cargo_types: list[str] | None = None
    lead_score: int | None = None
    raw_payload: dict | None = None


class CarrierSnapshotCreate(CarrierSnapshotBase):
    pass


class CarrierSnapshotRead(CarrierSnapshotBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class CarrierSnapshotStatsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    snapshot_date: date
    fleet_size: int | None = None
    power_units: int | None = None
    authority_status: str | None = None
    lead_score: float | None = None


class CarrierStatsResponse(BaseModel):
    carrier_id: int
    snapshots: list[CarrierSnapshotStatsRead]


class OutreachStatusUpdate(BaseModel):
    status: OutreachStatus


class OutreachNoteCreate(BaseModel):
    content: str = Field(validation_alias=AliasChoices("content", "note"))
    outcome: str | None = None
    follow_up_date: datetime | None = None
    dispatcher_name: str | None = None


class OutreachNoteUpdate(BaseModel):
    content: str | None = Field(
        default=None,
        validation_alias=AliasChoices("content", "note"),
    )
    outcome: str | None = None
    follow_up_date: datetime | None = None


class OutreachNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    carrier_id: int
    content: str = Field(validation_alias=AliasChoices("content", "note"))
    outcome: str | None
    follow_up_date: datetime | None
    contact_name: str | None
    dispatcher_name: str | None
    pain_points: str | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime


class TagBase(BaseModel):
    name: str
    display_name: str | None = None


class TagCreate(TagBase):
    pass


class TagAddRequest(BaseModel):
    tag_id: int


class TagRead(TagBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class CarrierPipelineStats(BaseModel):
    total: int
    new_last_30_days: int
    avg_lead_score: float | None
    not_contacted: int
