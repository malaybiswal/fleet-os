from app.schemas.load_evaluation import (
    LoadEvaluationRequest,
    LoadEvaluationResponse,
    LoadEvaluationMetrics,
)


DEFAULT_MPG = 7.0
DEFAULT_DIESEL_PRICE = 4.00
DEFAULT_AVG_SPEED_MPH = 55.0


def evaluate_load(request: LoadEvaluationRequest) -> LoadEvaluationResponse:
    total_miles = request.loaded_miles + request.deadhead_miles

    gross_rpm = request.payout / request.loaded_miles
    deadhead_adjusted_rpm = request.payout / total_miles

    estimated_fuel_cost = (total_miles / DEFAULT_MPG) * DEFAULT_DIESEL_PRICE

    estimated_drive_hours = total_miles / DEFAULT_AVG_SPEED_MPH
    estimated_revenue_per_hour = request.payout / estimated_drive_hours

    deadhead_percent = request.deadhead_miles / total_miles
    deadhead_penalty = deadhead_percent * 100

    operational_score = _calculate_operational_score(
        deadhead_adjusted_rpm=deadhead_adjusted_rpm,
        deadhead_percent=deadhead_percent,
        estimated_revenue_per_hour=estimated_revenue_per_hour,
    )

    recommendation, reasons = _recommend(
        deadhead_adjusted_rpm=deadhead_adjusted_rpm,
        deadhead_percent=deadhead_percent,
        estimated_revenue_per_hour=estimated_revenue_per_hour,
        operational_score=operational_score,
    )

    return LoadEvaluationResponse(
        recommendation=recommendation,
        metrics=LoadEvaluationMetrics(
            gross_rpm=round(gross_rpm, 2),
            deadhead_adjusted_rpm=round(deadhead_adjusted_rpm, 2),
            estimated_fuel_cost=round(estimated_fuel_cost, 2),
            estimated_revenue_per_hour=round(estimated_revenue_per_hour, 2),
            deadhead_penalty=round(deadhead_penalty, 1),
            operational_score=operational_score,
        ),
        reasons=reasons,
    )


def _calculate_operational_score(
    deadhead_adjusted_rpm: float,
    deadhead_percent: float,
    estimated_revenue_per_hour: float,
) -> int:
    score = 50

    if deadhead_adjusted_rpm >= 2.5:
        score += 25
    elif deadhead_adjusted_rpm >= 2.0:
        score += 15
    elif deadhead_adjusted_rpm < 1.5:
        score -= 25

    if deadhead_percent <= 0.15:
        score += 15
    elif deadhead_percent <= 0.30:
        score += 5
    else:
        score -= 20

    if estimated_revenue_per_hour >= 150:
        score += 10
    elif estimated_revenue_per_hour < 90:
        score -= 10

    return max(0, min(100, score))


def _recommend(
    deadhead_adjusted_rpm: float,
    deadhead_percent: float,
    estimated_revenue_per_hour: float,
    operational_score: int,
) -> tuple[str, list[str]]:
    reasons = []

    if deadhead_adjusted_rpm >= 2.2:
        reasons.append("Strong deadhead-adjusted RPM")
    elif deadhead_adjusted_rpm < 1.6:
        reasons.append("Weak deadhead-adjusted RPM")
    else:
        reasons.append("Deadhead-adjusted RPM requires review")

    if deadhead_percent <= 0.20:
        reasons.append("Deadhead exposure is acceptable")
    elif deadhead_percent > 0.35:
        reasons.append("High deadhead exposure reduces profitability")
    else:
        reasons.append("Deadhead exposure requires dispatcher review")

    if estimated_revenue_per_hour >= 140:
        reasons.append("Estimated revenue per hour is strong")
    elif estimated_revenue_per_hour < 90:
        reasons.append("Estimated revenue per hour is weak")
    else:
        reasons.append("Estimated revenue per hour requires review")

    if operational_score >= 75:
        reasons.append("Overall operational score supports taking this load")
        return "TAKE", reasons

    if operational_score <= 45:
        reasons.append("Overall operational score indicates high operational risk")
        return "AVOID", reasons

    reasons.append("Operational score requires dispatcher review")
    return "REVIEW", reasons
