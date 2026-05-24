from app.ingestion.normalized_events import (
    NormalizedEventType,
)
from app.integrations.simulator.mapper import (
    map_simulator_payload_to_event,
)


def test_map_simulator_payload_to_event():
    payload = {
        "vehicle_id": "SIM-001",
        "fleet_id": 17,
        "timestamp": "2026-01-01T12:00:00+00:00",
        "location": {
            "description": "Austin, TX",
            "lat": 30.2672,
            "lon": -97.7431,
        },
        "speed_mph": 65.5,
        "status": "active",
    }

    event = map_simulator_payload_to_event(payload)

    assert event.event_type == NormalizedEventType.TELEMETRY
    assert event.truck_id == "SIM-001"
    assert event.fleet_id == 17
    assert event.latitude == 30.2672
    assert event.longitude == -97.7431
    assert event.source == "simulator"
