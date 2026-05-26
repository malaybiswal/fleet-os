from datetime import datetime

from app.ingestion.normalized_events import (
    NormalizedTelemetryEvent,
)


def map_simulator_payload_to_event(
    payload: dict,
) -> NormalizedTelemetryEvent:
    return NormalizedTelemetryEvent(
        fleet_id=payload["fleet_id"],
        truck_id=payload["vehicle_id"],
        timestamp=datetime.fromisoformat(payload["timestamp"]),
        latitude=payload["location"]["lat"],
        longitude=payload["location"]["lon"],
        speed_mph=payload["speed_mph"],
        heading=payload.get("heading"),
        location_description=payload["location"]["description"],
        status=payload["status"],
        source="simulator",
        raw_payload=payload,
    )
