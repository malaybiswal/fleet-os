from datetime import datetime, timezone

from app.ingestion.normalized_events import (
    NormalizedEventType,
    NormalizedTelemetryEvent,
)


def test_normalized_telemetry_event_defaults_event_type():
    event = NormalizedTelemetryEvent(
        fleet_id=1,
        truck_id="TRUCK-001",
        timestamp=datetime.now(timezone.utc),
        latitude=30.506,
        longitude=-97.8305,
        source="simulator",
    )

    assert event.event_type == NormalizedEventType.TELEMETRY
    assert event.fleet_id == 1
    assert event.truck_id == "TRUCK-001"
    assert event.source == "simulator"


def test_normalized_telemetry_event_preserves_raw_payload():
    event = NormalizedTelemetryEvent(
        fleet_id=1,
        truck_id="TRUCK-001",
        timestamp=datetime.now(timezone.utc),
        source="mock_motive",
        raw_payload={"vehicle_id": 999999, "number": "Truck-01"},
    )

    assert event.raw_payload["vehicle_id"] == 999999
