from pydantic import BaseModel, Field


class LoadEvaluationRequest(BaseModel):
    payout: float = Field(gt=0)
    loaded_miles: float = Field(gt=0)
    deadhead_miles: float = Field(ge=0)
    equipment_type: str
    fuel_cost: float | None = Field(default=None, ge=0)
    maintenance_reserve: float | None = Field(default=None, ge=0)
    driver_cost: float | None = Field(default=None, ge=0)
    tolls: float | None = Field(default=None, ge=0)
    expected_dwell_hours: float = Field(default=0, ge=0)


class LoadEvaluationScoreFactors(BaseModel):
    margin_score: float
    net_rpm_score: float
    revenue_per_hour_score: float


class LoadEvaluationMetrics(BaseModel):
    gross_rpm: float
    deadhead_adjusted_rpm: float
    estimated_fuel_cost: float
    estimated_revenue_per_hour: float
    estimated_drive_hours: float
    expected_dwell_hours: float
    deadhead_penalty: float
    profitability_score: float
    # Backward-compatible alias for older consumers while the UI migrates to
    # profitability/final dispatch terminology.
    operational_score: float
    profitability_factors: LoadEvaluationScoreFactors
    net_margin: float
    stored_costs_used: bool


class LoadEvaluationResponse(BaseModel):
    recommendation: str
    metrics: LoadEvaluationMetrics
    reasons: list[str]
