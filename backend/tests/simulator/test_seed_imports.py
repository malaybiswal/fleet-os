from simulator.generators import (
    generate_alerts,
    generate_drivers,
    generate_dwell_events,
    generate_loads,
    generate_telemetry_events,
    generate_trucks,
)
from simulator.seed import parse_date


def test_simulator_imports():
    assert generate_alerts is not None
    assert generate_drivers is not None
    assert generate_dwell_events is not None
    assert generate_loads is not None
    assert generate_telemetry_events is not None
    assert generate_trucks is not None


def test_parse_date_returns_utc_datetime():
    parsed = parse_date("2024-11-01")

    assert parsed.year == 2024
    assert parsed.month == 11
    assert parsed.day == 1
    assert parsed.tzinfo is not None


def test_generate_trucks_count():
    trucks = generate_trucks(3)

    assert len(trucks) == 3
    assert trucks[0].truck_id.startswith("TRUCK-")


def test_generate_drivers_count():
    drivers = generate_drivers(3)

    assert len(drivers) == 3
    assert drivers[0].driver_id.startswith("DRIVER-")