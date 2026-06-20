from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.facility import FacilityRiskSummary
from app.schemas.load import LoadResponse

DispatcherRecommendation = Literal["RECOMMENDED", "REVIEW", "AVOID"]


class DispatcherScoreBreakdown(BaseModel):
    profitability_baseline: float
    facility_multiplier: float
    broker_multiplier: float
    alert_penalty: float
    strategy_bonus: float
    final_dispatch_score: float


class DispatcherDecisionMetrics(BaseModel):
    gross_rpm: float
    deadhead_adjusted_rpm: float
    estimated_fuel_cost: float
    estimated_revenue_per_hour: float
    estimated_drive_hours: float
    expected_dwell_hours: float | None = None
    deadhead_penalty: float
    profitability_score: float
    # Backward-compatible alias while older consumers migrate.
    operational_score: float
    deadhead_miles: float
    net_margin: float
    stored_costs_used: bool
    broker_risk_band: str
    facility_detention_risk_band: str | None = None
    profitability_baseline: float | None = None
    facility_multiplier: float | None = None
    broker_multiplier: float | None = None
    alert_penalty: float | None = None
    strategy_bonus: float | None = None
    final_dispatch_score: float | None = None


class DispatcherTruckOption(BaseModel):
    truck_id: str
    driver_id: str
    driver_name: str
    driver_hos_hours_remaining: float | None = None
    status: str
    current_location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    last_seen_at: datetime | None = None
    active_alert_count: int = 0
    highest_alert_severity: str | None = None
    recommendation: DispatcherRecommendation
    rank_score: float
    deadhead_miles: float
    deadhead_source: str
    can_make_pickup: bool
    estimated_revenue_per_hour: float
    profitability_score: float
    # Backward-compatible alias while older consumers migrate.
    operational_score: float
    score_breakdown: DispatcherScoreBreakdown
    reasons: list[str]
    ranking_factors: list[str]


class DispatcherAssignmentRequest(BaseModel):
    truck_id: str
    driver_id: str


class DispatcherCommandCenterDecision(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    load: LoadResponse
    best_truck: DispatcherTruckOption | None = None
    truck_options: list[DispatcherTruckOption]
    facility_risk: FacilityRiskSummary | None = None
    final_recommendation: DispatcherRecommendation
    metrics: DispatcherDecisionMetrics
    reasons: list[str]
    decision_notes: list[str]
    is_candidate: bool
