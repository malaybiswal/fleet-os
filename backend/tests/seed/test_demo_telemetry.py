from datetime import datetime, timezone

from app.seed.demo_dataset import build_demo_dataset
from app.simulator.telemetry import DEMO_TELEMETRY_EVENT_COUNTS


BASE_DATE = datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc)


def test_moving_routes_interpolate_coordinates():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)

    events = _events_for(dataset, "DEMO-TRUCK-001")

    assert events[0].latitude > events[-1].latitude
    assert events[0].longitude < events[-1].longitude
    assert events[0].speed > 20
    assert events[-1].speed > 20


def test_stopped_and_maintenance_timelines_keep_stable_coordinates_and_zero_speed():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)

    for truck_id in ("DEMO-TRUCK-003", "DEMO-TRUCK-005"):
        events = _events_for(dataset, truck_id)
        latitudes = {event.latitude for event in events}
        longitudes = {event.longitude for event in events}
        speeds = {event.speed for event in events}

        assert len(latitudes) == 1
        assert len(longitudes) == 1
        assert speeds == {0}


def test_idle_timeline_uses_idle_speeds_and_increasing_idle_minutes():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)
    events = _events_for(dataset, "DEMO-TRUCK-006")

    assert events[0].speed == 0
    assert events[-1].speed == 3
    assert events[-1].idle_minutes > events[0].idle_minutes
    assert all(event.reported_status == "idle" for event in events)


def test_high_dwell_timeline_remains_stopped_for_seven_hours():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)
    events = _events_for(dataset, "DEMO-TRUCK-003")
    duration_hours = (events[-1].timestamp - events[0].timestamp).total_seconds() / 3600

    assert len(events) == DEMO_TELEMETRY_EVENT_COUNTS["DEMO-TRUCK-003"]
    assert duration_hours == 7
    assert {event.speed for event in events} == {0}
    assert {event.reported_status for event in events} == {"stopped"}


def _events_for(dataset, truck_id):
    return [
        event
        for event in dataset.telemetry_events
        if event.truck_id == truck_id
    ]
