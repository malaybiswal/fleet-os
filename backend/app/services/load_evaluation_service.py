from dataclasses import dataclass

from app.schemas.load_evaluation import (
    LoadEvaluationRequest,
    LoadEvaluationResponse,
    LoadEvaluationMetrics,
    LoadEvaluationScoreFactors,
)


DEFAULT_MPG = 7.0
DEFAULT_DIESEL_PRICE = 4.00
DEFAULT_AVG_SPEED_MPH = 55.0


@dataclass(frozen=True)
class ProfitabilityScoreBreakdown:
    score: float
    margin_score: float
    net_rpm_score: float
    revenue_per_hour_score: float
    reasons: list[str]


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def linear_score(
    value: float,
    floor: float,
    ceiling: float,
    *,
    minimum_score: float = 0.0,
    maximum_score: float = 100.0,
) -> float:
    """Scale a value continuously between a bounded score range."""
    if ceiling == floor:
        return maximum_score if value >= ceiling else minimum_score

    ratio = (value - floor) / (ceiling - floor)
    return clamp(
        minimum_score + ratio * (maximum_score - minimum_score),
        minimum_score,
        maximum_score,
    )


def evaluate_load(request: LoadEvaluationRequest) -> LoadEvaluationResponse:
    total_miles = request.loaded_miles + request.deadhead_miles

    gross_rpm = request.payout / request.loaded_miles
    deadhead_adjusted_rpm = request.payout / total_miles

    fallback_fuel_cost = (total_miles / DEFAULT_MPG) * DEFAULT_DIESEL_PRICE
    estimated_fuel_cost = request.fuel_cost if request.fuel_cost is not None else fallback_fuel_cost
    stored_costs_used = _has_stored_costs(request)
    net_margin = request.payout - (
        estimated_fuel_cost
        + (request.maintenance_reserve or 0)
        + (request.driver_cost or 0)
        + (request.tolls or 0)
    )

    estimated_drive_hours = total_miles / DEFAULT_AVG_SPEED_MPH
    expected_dwell_hours = request.expected_dwell_hours or 0.0
    estimated_engine_hours = estimated_drive_hours + expected_dwell_hours
    estimated_revenue_per_hour = request.payout / estimated_engine_hours

    deadhead_percent = request.deadhead_miles / total_miles
    deadhead_penalty = deadhead_percent * 100

    profitability = _calculate_profitability_score(
        payout=request.payout,
        net_margin=net_margin,
        deadhead_adjusted_rpm=deadhead_adjusted_rpm,
        estimated_revenue_per_hour=estimated_revenue_per_hour,
    )

    recommendation, reasons = _recommend(
        deadhead_adjusted_rpm=deadhead_adjusted_rpm,
        deadhead_percent=deadhead_percent,
        estimated_revenue_per_hour=estimated_revenue_per_hour,
        profitability=profitability,
    )

    return LoadEvaluationResponse(
        recommendation=recommendation,
        metrics=LoadEvaluationMetrics(
            gross_rpm=round(gross_rpm, 2),
            deadhead_adjusted_rpm=round(deadhead_adjusted_rpm, 2),
            estimated_fuel_cost=round(estimated_fuel_cost, 2),
            estimated_revenue_per_hour=round(estimated_revenue_per_hour, 2),
            estimated_drive_hours=round(estimated_drive_hours, 2),
            expected_dwell_hours=round(expected_dwell_hours, 2),
            deadhead_penalty=round(deadhead_penalty, 1),
            profitability_score=round(profitability.score, 2),
            operational_score=round(profitability.score, 2),
            profitability_factors=LoadEvaluationScoreFactors(
                margin_score=round(profitability.margin_score, 2),
                net_rpm_score=round(profitability.net_rpm_score, 2),
                revenue_per_hour_score=round(profitability.revenue_per_hour_score, 2),
            ),
            net_margin=round(net_margin, 2),
            stored_costs_used=stored_costs_used,
        ),
        reasons=reasons,
    )


def _has_stored_costs(request: LoadEvaluationRequest) -> bool:
    return any(
        value is not None
        for value in (
            request.fuel_cost,
            request.maintenance_reserve,
            request.driver_cost,
            request.tolls,
        )
    )


def _calculate_profitability_score(
    *,
    payout: float,
    net_margin: float,
    deadhead_adjusted_rpm: float,
    estimated_revenue_per_hour: float,
) -> ProfitabilityScoreBreakdown:
    margin_pct = net_margin / payout
    margin_score = linear_score(margin_pct, 0.05, 0.45)
    net_rpm_score = linear_score(deadhead_adjusted_rpm, 1.35, 3.0)
    revenue_per_hour_score = linear_score(estimated_revenue_per_hour, 75, 160)

    score = (
        0.30 * margin_score
        + 0.45 * net_rpm_score
        + 0.25 * revenue_per_hour_score
    )

    return ProfitabilityScoreBreakdown(
        score=round(clamp(score), 2),
        margin_score=margin_score,
        net_rpm_score=net_rpm_score,
        revenue_per_hour_score=revenue_per_hour_score,
        reasons=[
            f"Net margin contributes {margin_score:.0f}/100 to profitability",
            f"Deadhead-adjusted RPM contributes {net_rpm_score:.0f}/100 to profitability",
            f"Revenue per engine hour contributes {revenue_per_hour_score:.0f}/100 to profitability",
        ],
    )


def _recommend(
    deadhead_adjusted_rpm: float,
    deadhead_percent: float,
    estimated_revenue_per_hour: float,
    profitability: ProfitabilityScoreBreakdown,
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
        reasons.append("Estimated revenue per engine hour is strong")
    elif estimated_revenue_per_hour < 90:
        reasons.append("Estimated revenue per engine hour is weak")
    else:
        reasons.append("Estimated revenue per engine hour requires review")

    reasons.extend(profitability.reasons)

    if profitability.score >= 80:
        reasons.append("Profitability score supports recommending this load")
        return "RECOMMENDED", reasons

    if profitability.score < 50:
        reasons.append("Profitability score indicates this load should be avoided")
        return "AVOID", reasons

    reasons.append("Profitability score requires dispatcher review")
    return "REVIEW", reasons
