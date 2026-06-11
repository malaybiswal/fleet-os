from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.dwell_event import DwellEventResponse


class FacilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str | None = None
    state: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    facility_type: str | None = None


class FacilityIntelligence(BaseModel):
    # facility_id is None for legacy dwell events not yet linked to a facility row
    facility_id: int | None = None
    facility_name: str
    city: str | None = None
    state: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    facility_type: str | None = None

    operational_score: float | None = None
    dwell_score: float | None = None
    avg_dwell_hours: float | None = None
    p90_dwell_hours: float | None = None
    appointment_reliability_pct: float | None = None
    avg_appointment_delay_hours: float | None = None
    detention_risk_score: float | None = None
    detention_risk_band: str | None = None
    total_detention_pay: Decimal = Decimal("0")
    visit_count: int = 0
    confidence: str = "low"
    last_visit_at: datetime | None = None


class FacilityDetail(FacilityIntelligence):
    recent_dwell_events: list[DwellEventResponse] = []
