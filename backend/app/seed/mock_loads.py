from datetime import datetime, timedelta
from decimal import Decimal
import random

from app.schemas.load_evaluation import LoadEvaluationRequest
from app.seed.mock_facilities import demo_facility_risk_summaries
from app.seed.scenarios import STRATEGIC_LOAD_SCENARIOS
from app.seed.types import LoadSeed
from app.services.load_evaluation_service import evaluate_load

STRATEGIC_MOCK_LOADS = [
    scenario.to_mock_load()
    for scenario in STRATEGIC_LOAD_SCENARIOS
]

# Destination facility for each strategic scenario, matching the load/facility
# assignments in build_demo_loads() and DEMO_DWELL_SCENARIOS below.
SCENARIO_DESTINATION_FACILITY = {
    "high_pay_bad_load": "Denver West DC",
    "low_pay_good_load": "Houston Crossdock",
    "high_dwell_risk": "Dallas Mega Cold Storage",
    "strong_reload_market": "Atlanta Reload Hub",
    "bad_deadhead": "Oklahoma Pipe Yard",
}


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
                equipment_type=scenario.equipment_type,
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
            revenue=Decimal("3400"),
            miles=Decimal("710"),
            deadhead_miles=Decimal("160"),
            fuel_cost=_money((1280 / 7.0) * 4.0, rng),
            maintenance_reserve=_money(1280 * 0.12, rng),
            driver_cost=_money(1280 * 0.72, rng),
            tolls=_money(35, rng),
            pickup_time=pickup_time,
            delivery_time=pickup_time + timedelta(hours=16),
            status="booked",
            equipment_type="Dry Van",
        )
    )

    # Unassigned candidate loads — available for dispatch evaluation.
    # These are the demo showcase loads for the Dispatcher Command Center (Phase 1+).
    # truck_id/driver_id are None; status="available" marks them as open opportunities.
    candidate_pickup = base_date + timedelta(hours=24)
    loads.append(
        LoadSeed(
            load_id="DEMO-CAND-GOOD",
            fleet_key="operations",
            truck_id=None,
            driver_id=None,
            scenario_key="low_pay_good_load",
            broker_name="CH Robinson",
            origin="Dallas, TX",
            destination="Houston, TX",
            revenue=Decimal("950"),
            miles=Decimal("260"),
            deadhead_miles=Decimal("20"),
            fuel_cost=_money((280 / 7.0) * 4.0, rng),
            maintenance_reserve=_money(280 * 0.12, rng),
            driver_cost=_money(280 * 0.72, rng),
            tolls=_money(18, rng),
            pickup_time=candidate_pickup,
            delivery_time=candidate_pickup + timedelta(hours=6),
            status="available",
            equipment_type="Dry Van",
            origin_lat=Decimal("32.776700"),
            origin_lon=Decimal("-96.797000"),
        )
    )
    loads.append(
        LoadSeed(
            load_id="DEMO-CAND-WEAK-BROKER",
            fleet_key="operations",
            truck_id=None,
            driver_id=None,
            scenario_key="weak_broker",
            broker_name="TQL Risk Desk",
            origin="El Paso, TX",
            destination="Phoenix, AZ",
            revenue=Decimal("3400"),
            miles=Decimal("710"),
            deadhead_miles=Decimal("160"),
            fuel_cost=_money((1280 / 7.0) * 4.0, rng),
            maintenance_reserve=_money(1280 * 0.12, rng),
            driver_cost=_money(1280 * 0.72, rng),
            tolls=_money(35, rng),
            pickup_time=candidate_pickup + timedelta(hours=4),
            delivery_time=candidate_pickup + timedelta(hours=20),
            status="available",
            equipment_type="Dry Van",
            origin_lat=Decimal("31.761900"),
            origin_lon=Decimal("-106.485000"),
        )
    )
    loads.append(
        LoadSeed(
            load_id="DEMO-CAND-BAD-DEADHEAD",
            fleet_key="operations",
            truck_id=None,
            driver_id=None,
            scenario_key="bad_deadhead",
            broker_name="TQL",
            origin="Amarillo, TX",
            destination="Oklahoma City, OK",
            revenue=Decimal("1800"),
            miles=Decimal("600"),
            deadhead_miles=Decimal("420"),
            fuel_cost=_money((1020 / 7.0) * 4.0, rng),
            maintenance_reserve=_money(1020 * 0.12, rng),
            driver_cost=_money(1020 * 0.72, rng),
            tolls=_money(28, rng),
            pickup_time=candidate_pickup + timedelta(hours=8),
            delivery_time=candidate_pickup + timedelta(hours=22),
            status="available",
            equipment_type="Flatbed",
            origin_lat=Decimal("35.221900"),
            origin_lon=Decimal("-101.831300"),
        )
    )

    return tuple(loads)


def get_evaluated_mock_loads() -> list[dict]:
    facility_risk_by_name = demo_facility_risk_summaries()
    evaluated_loads = []

    for scenario, load in zip(STRATEGIC_LOAD_SCENARIOS, STRATEGIC_MOCK_LOADS):
        request = LoadEvaluationRequest(
            payout=load["payout"],
            loaded_miles=load["loaded_miles"],
            deadhead_miles=load["deadhead_miles"],
            equipment_type=load["equipment_type"],
        )
        evaluation = evaluate_load(request)

        facility_name = SCENARIO_DESTINATION_FACILITY.get(scenario.key)
        facility_risk = facility_risk_by_name.get(facility_name) if facility_name else None

        evaluated_loads.append(
            {
                **load,
                "actual_recommendation": evaluation.recommendation,
                "metrics": evaluation.metrics.model_dump(),
                "reasons": evaluation.reasons,
                "destination_facility": facility_risk.model_dump() if facility_risk else None,
            }
        )

    return evaluated_loads


def _money(value: float, rng: random.Random) -> Decimal:
    adjusted = value + rng.uniform(-2.5, 2.5)
    return Decimal(str(round(max(0, adjusted), 2)))
