from app.schemas.load_evaluation import LoadEvaluationRequest
from app.services.load_evaluation_service import evaluate_load


def test_evaluate_good_load_recommends_recommended():
    result = evaluate_load(
        LoadEvaluationRequest(
            payout=2500,
            loaded_miles=900,
            deadhead_miles=80,
            equipment_type="Dry Van",
        )
    )

    assert result.recommendation == "RECOMMENDED"
    assert result.metrics.deadhead_adjusted_rpm > 2.0
    assert result.metrics.profitability_score >= 80
    assert result.metrics.operational_score == result.metrics.profitability_score


def test_evaluate_bad_deadhead_load_recommends_avoid():
    result = evaluate_load(
        LoadEvaluationRequest(
            payout=1200,
            loaded_miles=500,
            deadhead_miles=400,
            equipment_type="Dry Van",
        )
    )

    assert result.recommendation in {"AVOID", "REVIEW"}
    assert result.metrics.deadhead_penalty > 35


def test_evaluate_returns_required_metrics():
    result = evaluate_load(
        LoadEvaluationRequest(
            payout=1800,
            loaded_miles=700,
            deadhead_miles=100,
            equipment_type="Reefer",
        )
    )

    assert result.metrics.gross_rpm > 0
    assert result.metrics.deadhead_adjusted_rpm > 0
    assert result.metrics.estimated_fuel_cost > 0
    assert result.metrics.estimated_revenue_per_hour > 0
    assert 0 <= result.metrics.operational_score <= 100
    assert result.metrics.net_margin > 0
    assert result.metrics.stored_costs_used is False


def test_evaluate_uses_stored_costs_when_present():
    result = evaluate_load(
        LoadEvaluationRequest(
            payout=3000,
            loaded_miles=900,
            deadhead_miles=100,
            equipment_type="Dry Van",
            fuel_cost=500,
            maintenance_reserve=125,
            driver_cost=750,
            tolls=25,
        )
    )

    assert result.metrics.estimated_fuel_cost == 500
    assert result.metrics.net_margin == 1600
    assert result.metrics.stored_costs_used is True


def test_recommended_recommendation_includes_positive_reasoning():
    result = evaluate_load(
        LoadEvaluationRequest(
            payout=3000,
            loaded_miles=1000,
            deadhead_miles=50,
            equipment_type="Dry Van",
        )
    )

    assert result.recommendation == "RECOMMENDED"
    assert result.reasons
    assert "Profitability score supports recommending this load" in result.reasons
    assert any("deadhead" in reason.lower() for reason in result.reasons)


def test_avoid_recommendation_includes_risk_reasoning():
    result = evaluate_load(
        LoadEvaluationRequest(
            payout=1200,
            loaded_miles=700,
            deadhead_miles=500,
            equipment_type="Dry Van",
        )
    )

    assert result.recommendation == "AVOID"
    assert result.reasons
    assert "Profitability score indicates this load should be avoided" in result.reasons
    assert any("weak" in reason.lower() or "high" in reason.lower() for reason in result.reasons)


def test_review_recommendation_includes_dispatcher_review_reasoning():
    result = evaluate_load(
        LoadEvaluationRequest(
            payout=1800,
            loaded_miles=700,
            deadhead_miles=200,
            equipment_type="Reefer",
        )
    )

    assert result.recommendation == "REVIEW"
    assert result.reasons
    assert "Profitability score requires dispatcher review" in result.reasons


def test_recommendation_reasons_are_never_empty():
    result = evaluate_load(
        LoadEvaluationRequest(
            payout=1600,
            loaded_miles=650,
            deadhead_miles=180,
            equipment_type="Flatbed",
        )
    )

    assert result.reasons
    assert len(result.reasons) >= 3


def test_profitability_score_is_continuous_without_rpm_cliffs():
    just_below = evaluate_load(
        LoadEvaluationRequest(
            payout=1990,
            loaded_miles=900,
            deadhead_miles=100,
            equipment_type="Dry Van",
        )
    )
    just_above = evaluate_load(
        LoadEvaluationRequest(
            payout=2000,
            loaded_miles=900,
            deadhead_miles=100,
            equipment_type="Dry Van",
        )
    )

    assert abs(just_above.metrics.profitability_score - just_below.metrics.profitability_score) < 2
    assert just_below.metrics.profitability_factors.net_rpm_score < just_above.metrics.profitability_factors.net_rpm_score


def test_expected_dwell_reduces_revenue_per_engine_hour_and_profitability():
    without_dwell = evaluate_load(
        LoadEvaluationRequest(
            payout=2500,
            loaded_miles=900,
            deadhead_miles=80,
            equipment_type="Dry Van",
        )
    )
    with_dwell = evaluate_load(
        LoadEvaluationRequest(
            payout=2500,
            loaded_miles=900,
            deadhead_miles=80,
            equipment_type="Dry Van",
            expected_dwell_hours=6,
        )
    )

    assert with_dwell.metrics.expected_dwell_hours == 6
    assert with_dwell.metrics.estimated_revenue_per_hour < without_dwell.metrics.estimated_revenue_per_hour
    assert with_dwell.metrics.profitability_score < without_dwell.metrics.profitability_score
