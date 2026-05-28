from datetime import datetime, timedelta
from decimal import Decimal
import random

from app.schemas.load_evaluation import LoadEvaluationRequest
from app.seed.scenarios import STRATEGIC_LOAD_SCENARIOS
from app.seed.types import LoadSeed
from app.services.load_evaluation_service import evaluate_load

STRATEGIC_MOCK_LOADS = [
    scenario.to_mock_load()
    for scenario in STRATEGIC_LOAD_SCENARIOS
]


def build_demo_loads(
    base_date: datetime,
    rng: random.Random,
) -> tuple[LoadSeed, ...]:
    assignments = {
        "high_pay_bad_load": ("operations", "DEMO-TRUCK-002", "DEMO-DRIVER-002", "DEMO-LOAD-HIGH-PAY-BAD"),
        "low_pay_good_load": ("operations", "DEMO-TRUCK-001", "DEMO-DRIVER-001", "DEMO-LOAD-GOOD"),
        "high_dwell_risk": ("refrigerated", "DEMO-TRUCK-003", "DEMO-DRIVER-006", "DEMO-LOAD-HIGH-DWELL"),
        "strong_reload_market": ("operations", "DEMO-TRUCK-004", "DEMO-DRIVER-003", "DEMO-LOAD-STRONG-RELOAD"),
        "bad_deadhead": ("operations", "DEMO-TRUCK-005", "DEMO-DRIVER-004", "DEMO-LOAD-BAD-DEADHEAD"),
    }

    loads: list[LoadSeed] = []
    for index, scenario in enumerate(STRATEGIC_LOAD_SCENARIOS):
        fleet_key, truck_id, driver_id, load_id = assignments[scenario.key]
        total_miles = scenario.loaded_miles + scenario.deadhead_miles
        pickup_time = base_date + timedelta(hours=index * 3)
        delivery_time = pickup_time + timedelta(hours=max(4, round(total_miles / 50)))

        loads.append(
            LoadSeed(
                load_id=load_id,
                fleet_key=fleet_key,
                truck_id=truck_id,
                driver_id=driver_id,
                scenario_key=scenario.key,
                broker_name=scenario.broker_name,
                origin=scenario.origin,
                destination=scenario.destination,
                revenue=Decimal(str(scenario.payout)),
                miles=Decimal(str(scenario.loaded_miles)),
                deadhead_miles=Decimal(str(scenario.deadhead_miles)),
                fuel_cost=_money((total_miles / 7.0) * 4.0, rng),
                maintenance_reserve=_money(total_miles * 0.12, rng),
                driver_cost=_money(total_miles * 0.72, rng),
                tolls=_money(25 + index * 18, rng),
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                status="delivered" if scenario.key in {"low_pay_good_load", "strong_reload_market"} else "in_transit",
            )
        )

    pickup_time = base_date + timedelta(hours=17)
    loads.append(
        LoadSeed(
            load_id="DEMO-LOAD-WEAK-BROKER",
            fleet_key="operations",
            truck_id="DEMO-TRUCK-006",
            driver_id="DEMO-DRIVER-005",
            scenario_key="weak_broker",
            broker_name="TQL Risk Desk",
            origin="El Paso, TX",
            destination="Phoenix, AZ",
            revenue=Decimal("2150"),
            miles=Decimal("710"),
            deadhead_miles=Decimal("80"),
            fuel_cost=_money((790 / 7.0) * 4.0, rng),
            maintenance_reserve=_money(790 * 0.12, rng),
            driver_cost=_money(790 * 0.72, rng),
            tolls=_money(35, rng),
            pickup_time=pickup_time,
            delivery_time=pickup_time + timedelta(hours=16),
            status="booked",
        )
    )

    return tuple(loads)


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


def _money(value: float, rng: random.Random) -> Decimal:
    adjusted = value + rng.uniform(-2.5, 2.5)
    return Decimal(str(round(max(0, adjusted), 2)))
