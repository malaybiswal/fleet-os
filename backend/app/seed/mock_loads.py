from app.schemas.load_evaluation import LoadEvaluationRequest
from app.services.load_evaluation_service import evaluate_load

STRATEGIC_MOCK_LOADS = [
    {
        "name": "High Pay / Bad Load",
        "description": "Looks attractive because of payout, but weak after deadhead and time risk.",
        "payout": 4200,
        "loaded_miles": 1500,
        "deadhead_miles": 550,
        "equipment_type": "Dry Van",
        "expected_recommendation": "AVOID",
    },
    {
        "name": "Low Pay / Good Load",
        "description": "Lower gross payout, but short miles and low deadhead make it operationally strong.",
        "payout": 950,
        "loaded_miles": 260,
        "deadhead_miles": 20,
        "equipment_type": "Dry Van",
        "expected_recommendation": "TAKE",
    },
    {
        "name": "High Dwell Risk",
        "description": "Acceptable mileage economics, but demo scenario represents risky facility dwell.",
        "payout": 2400,
        "loaded_miles": 850,
        "deadhead_miles": 90,
        "equipment_type": "Reefer",
        "expected_recommendation": "REVIEW",
    },
    {
        "name": "Strong Reload Market",
        "description": "Good operational economics and strong destination reload opportunity.",
        "payout": 3100,
        "loaded_miles": 1050,
        "deadhead_miles": 60,
        "equipment_type": "Dry Van",
        "expected_recommendation": "TAKE",
    },
    {
        "name": "Bad Deadhead",
        "description": "Gross RPM looks acceptable, but deadhead destroys profitability.",
        "payout": 1800,
        "loaded_miles": 600,
        "deadhead_miles": 420,
        "equipment_type": "Flatbed",
        "expected_recommendation": "AVOID",
    },
]


def get_evaluated_mock_loads() -> list[dict]:
    evaluated_loads = []

    for load in STRATEGIC_MOCK_LOADS:
        request = LoadEvaluationRequest(
            payout=load["payout"],
            loaded_miles=load["loaded_miles"],
            deadhead_miles=load["deadhead_miles"],
            equipment_type=load["equipment_type"],
        )
        evaluation = evaluate_load(request)

        evaluated_loads.append(
            {
                **load,
                "actual_recommendation": evaluation.recommendation,
                "metrics": evaluation.metrics.model_dump(),
                "reasons": evaluation.reasons,
            }
        )

    return evaluated_loads

