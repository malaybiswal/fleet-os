from datetime import datetime, timezone
import random

from app.seed.mock_facilities import (
    DEMO_DWELL_SCENARIOS,
    DEMO_FACILITIES,
    DEMO_FACILITY_VISIT_PLANS,
    build_demo_dwell_events,
    build_demo_facility_history_loads,
)
from app.seed.mock_fleets import DEMO_FLEETS, DEMO_FLEET_NAMES
from app.seed.mock_loads import STRATEGIC_MOCK_LOADS, build_demo_loads
from app.seed.mock_trucks import DEMO_DRIVERS, build_demo_trucks_from_latest_telemetry
from app.simulator.telemetry import build_demo_telemetry_events


BASE_DATE = datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc)


def test_seed_modules_expose_repeatable_demo_data():
    rng = random.Random(32032)
    telemetry_events = build_demo_telemetry_events(BASE_DATE, rng)

    assert [fleet.name for fleet in DEMO_FLEETS] == list(DEMO_FLEET_NAMES)
    assert len(DEMO_DRIVERS) == 7
    assert len(STRATEGIC_MOCK_LOADS) == 5
    assert len(DEMO_DWELL_SCENARIOS) == 6
    assert len(DEMO_FACILITIES) == 6
    assert len(build_demo_loads(BASE_DATE, rng)) == 9  # 5 strategic + 1 weak-broker + 3 candidates

    total_visits = sum(len(visits) for visits in DEMO_FACILITY_VISIT_PLANS.values())
    extra_visits = total_visits - len(DEMO_DWELL_SCENARIOS)
    assert len(build_demo_dwell_events(BASE_DATE, rng)) == total_visits
    assert len(build_demo_facility_history_loads(BASE_DATE, rng)) == extra_visits
    assert len(build_demo_trucks_from_latest_telemetry(telemetry_events)) == 7
