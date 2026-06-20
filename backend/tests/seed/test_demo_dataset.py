from collections import Counter
from datetime import datetime, timezone

from app.seed.demo_dataset import build_demo_dataset
from app.seed.mock_fleets import DEMO_ID_PREFIX
from app.seed.scenarios import DEMO_SCENARIOS
from app.simulator.telemetry import (
    DEMO_TELEMETRY_EVENT_COUNTS,
    DEMO_TELEMETRY_EVENT_TOTAL,
    TELEMETRY_INTERVAL_MINUTES,
)


BASE_DATE = datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc)


def test_demo_dataset_generation_is_deterministic():
    first = build_demo_dataset(seed=32032, base_date=BASE_DATE)
    second = build_demo_dataset(seed=32032, base_date=BASE_DATE)

    assert first == second


def test_demo_dataset_uses_stable_demo_identifiers():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)

    assert all(driver.driver_id.startswith(DEMO_ID_PREFIX) for driver in dataset.drivers)
    assert all(truck.truck_id.startswith(DEMO_ID_PREFIX) for truck in dataset.trucks)
    assert all(load.load_id.startswith(DEMO_ID_PREFIX) for load in dataset.loads)


def test_required_demo_scenarios_are_defined():
    names = {scenario.name for scenario in DEMO_SCENARIOS}

    assert "Low Pay / Good Load" in names
    assert "Bad Deadhead" in names
    assert "High Dwell Risk" in names
    assert "Weak Broker" in names
    assert "Live Alerting Route" in names
    assert "Maintenance Truck" in names
    assert "Idle / Stopped Truck" in names


def test_demo_dataset_covers_operational_statuses():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)
    statuses = {truck.status for truck in dataset.trucks}

    assert {"stopped", "idle", "slow", "moving", "maintenance"}.issubset(statuses)


def test_demo_dataset_builds_expected_telemetry_history_volume():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)
    counts = Counter(event.truck_id for event in dataset.telemetry_events)

    assert len(dataset.telemetry_events) == DEMO_TELEMETRY_EVENT_TOTAL
    assert counts == DEMO_TELEMETRY_EVENT_COUNTS


def test_candidate_loads_exist_with_null_assignment():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)

    candidates = [load for load in dataset.loads if load.status == "available"]
    candidate_ids = {load.load_id for load in candidates}

    assert {"DEMO-CAND-GOOD", "DEMO-CAND-WEAK-BROKER", "DEMO-CAND-BAD-DEADHEAD"} == candidate_ids
    for load in candidates:
        assert load.truck_id is None
        assert load.driver_id is None
        assert load.equipment_type is not None
        assert load.origin_lat is not None
        assert load.origin_lon is not None


def test_strategic_loads_have_equipment_type():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)

    strategic_ids = {"DEMO-LOAD-GOOD", "DEMO-LOAD-HIGH-PAY-BAD", "DEMO-LOAD-HIGH-DWELL",
                     "DEMO-LOAD-STRONG-RELOAD", "DEMO-LOAD-BAD-DEADHEAD", "DEMO-LOAD-WEAK-BROKER"}
    strategic = [load for load in dataset.loads if load.load_id in strategic_ids]

    assert len(strategic) == len(strategic_ids)
    for load in strategic:
        assert load.equipment_type is not None, f"{load.load_id} missing equipment_type"


def test_demo_drivers_have_hos():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)

    demo_drivers = [d for d in dataset.drivers if d.driver_id.startswith("DEMO-DRIVER-")]
    assert len(demo_drivers) == 7
    for driver in demo_drivers:
        assert driver.hos_hours_remaining is not None

    driver_005 = next(d for d in demo_drivers if d.driver_id == "DEMO-DRIVER-005")
    assert float(driver_005.hos_hours_remaining) < 3.0


def test_demo_telemetry_timestamps_are_ordered_at_fixed_intervals():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)

    for truck_id in DEMO_TELEMETRY_EVENT_COUNTS:
        events = [
            event
            for event in dataset.telemetry_events
            if event.truck_id == truck_id
        ]

        assert events == sorted(events, key=lambda event: event.timestamp)
        for previous, current in zip(events, events[1:]):
            assert (
                current.timestamp - previous.timestamp
            ).total_seconds() == TELEMETRY_INTERVAL_MINUTES * 60
