from pydantic import BaseModel, Field


class LoadEvaluationRequest(BaseModel):
    payout: float = Field(gt=0)
    loaded_miles: float = Field(gt=0)
    deadhead_miles: float = Field(ge=0)
    equipment_type: str


class LoadEvaluationMetrics(BaseModel):
    gross_rpm: float
    deadhead_adjusted_rpm: float
    estimated_fuel_cost: float
    estimated_revenue_per_hour: float
    deadhead_penalty: float
    operational_score: int


class LoadEvaluationResponse(BaseModel):
    recommendation: str
    metrics: LoadEvaluationMetrics
    reasons: list[str]
