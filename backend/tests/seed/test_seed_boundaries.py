from datetime import datetime, timezone
import random

from app.seed.mock_alerts import build_demo_alerts
from app.seed.mock_facilities import DEMO_DWELL_SCENARIOS, build_demo_dwell_events
from app.seed.mock_fleets import DEMO_FLEETS, DEMO_FLEET_NAMES
from app.seed.mock_loads import STRATEGIC_MOCK_LOADS, build_demo_loads
from app.seed.mock_trucks import DEMO_DRIVERS, build_demo_trucks_from_latest_telemetry
from app.simulator.telemetry import build_demo_telemetry_events


BASE_DATE = datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc)


def test_seed_modules_expose_repeatable_demo_data():
    rng = random.Random(32032)
    telemetry_events = build_demo_telemetry_events(BASE_DATE, rng)

    assert [fleet.name for fleet in DEMO_FLEETS] == list(DEMO_FLEET_NAMES)
    assert len(DEMO_DRIVERS) == 6
    assert len(STRATEGIC_MOCK_LOADS) == 5
    assert len(DEMO_DWELL_SCENARIOS) == 6
    assert len(build_demo_loads(BASE_DATE, rng)) == 6
    assert len(build_demo_dwell_events(BASE_DATE, rng)) == 6
    assert len(build_demo_alerts(BASE_DATE)) == 5
    assert len(build_demo_trucks_from_latest_telemetry(telemetry_events)) == 6
