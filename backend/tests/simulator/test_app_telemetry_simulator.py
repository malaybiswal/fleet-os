from datetime import datetime, timezone
import random

from app.simulator.telemetry import (
    DEMO_TELEMETRY_EVENT_COUNTS,
    DEMO_TELEMETRY_EVENT_TOTAL,
    TELEMETRY_INTERVAL_MINUTES,
    build_demo_telemetry_events,
)


BASE_DATE = datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc)


def test_app_simulator_builds_expected_telemetry_volume():
    events = build_demo_telemetry_events(BASE_DATE, random.Random(32032))

    assert len(events) == DEMO_TELEMETRY_EVENT_TOTAL
    for truck_id, expected_count in DEMO_TELEMETRY_EVENT_COUNTS.items():
        assert len(_events_for(events, truck_id)) == expected_count


def test_app_simulator_timestamps_are_ordered_at_fixed_intervals():
    events = build_demo_telemetry_events(BASE_DATE, random.Random(32032))

    for truck_id in DEMO_TELEMETRY_EVENT_COUNTS:
        truck_events = _events_for(events, truck_id)
        assert truck_events == sorted(truck_events, key=lambda event: event.timestamp)
        for previous, current in zip(truck_events, truck_events[1:]):
            assert (
                current.timestamp - previous.timestamp
            ).total_seconds() == TELEMETRY_INTERVAL_MINUTES * 60


def test_app_simulator_interpolates_moving_routes():
    events = build_demo_telemetry_events(BASE_DATE, random.Random(32032))
    moving_events = _events_for(events, "DEMO-TRUCK-001")

    assert moving_events[0].latitude > moving_events[-1].latitude
    assert moving_events[0].longitude < moving_events[-1].longitude
    assert moving_events[-1].speed > 20


def test_app_simulator_keeps_stopped_and_maintenance_coordinates_stable():
    events = build_demo_telemetry_events(BASE_DATE, random.Random(32032))

    for truck_id in ("DEMO-TRUCK-003", "DEMO-TRUCK-005"):
        truck_events = _events_for(events, truck_id)
        assert len({event.latitude for event in truck_events}) == 1
        assert len({event.longitude for event in truck_events}) == 1
        assert {event.speed for event in truck_events} == {0}


def test_app_simulator_idle_timeline_accumulates_idle_minutes():
    events = build_demo_telemetry_events(BASE_DATE, random.Random(32032))
    idle_events = _events_for(events, "DEMO-TRUCK-006")

    assert idle_events[0].speed == 0
    assert idle_events[-1].speed == 3
    assert idle_events[-1].idle_minutes > idle_events[0].idle_minutes


def _events_for(events, truck_id):
    return [
        event
        for event in events
        if event.truck_id == truck_id
    ]
