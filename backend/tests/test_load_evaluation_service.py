from app.schemas.load_evaluation import LoadEvaluationRequest
from app.services.load_evaluation_service import evaluate_load


def test_evaluate_good_load_recommends_take():
    result = evaluate_load(
        LoadEvaluationRequest(
            payout=2500,
            loaded_miles=900,
            deadhead_miles=80,
            equipment_type="Dry Van",
        )
    )

    assert result.recommendation == "TAKE"
    assert result.metrics.deadhead_adjusted_rpm > 2.0
    assert result.metrics.operational_score >= 75


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
