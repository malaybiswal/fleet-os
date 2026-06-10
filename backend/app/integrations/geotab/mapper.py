from datetime import datetime, timezone
from typing import Any

from app.ingestion.normalized_events import NormalizedTelemetryEvent
from app.services.operational_status import derive_operational_status


KMH_TO_MPH = 0.621371


class GeotabMappingError(ValueError):
    pass


def map_device_status_info_to_event(
    payload: dict[str, Any],
    *,
    fleet_id: int,
) -> NormalizedTelemetryEvent:
    device_id = _device_id(payload)
    timestamp = _parse_timestamp(_required(payload, "dateTime"))
    speed_mph = _speed_mph(payload.get("speed"))

    return NormalizedTelemetryEvent(
        fleet_id=fleet_id,
        truck_id=f"GEOTAB-{fleet_id}-{device_id}",
        timestamp=timestamp,
        latitude=_optional_float(payload.get("latitude")),
        longitude=_optional_float(payload.get("longitude")),
        speed_mph=speed_mph,
        heading=_optional_int(payload.get("bearing")),
        status=derive_operational_status(speed_mph=speed_mph),
        source="geotab",
        source_event_id=f"geotab:{device_id}:{timestamp.isoformat()}",
        raw_payload=payload,
    )


def _device_id(payload: dict[str, Any]) -> str:
    device = _required(payload, "device")
    if not isinstance(device, dict):
        raise GeotabMappingError("DeviceStatusInfo device must be an object")

    device_id = device.get("id")
    if not device_id:
        raise GeotabMappingError("DeviceStatusInfo device.id is required")

    return str(device_id)


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise GeotabMappingError("DeviceStatusInfo dateTime must be a string")

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _speed_mph(value: Any) -> float | None:
    speed_kmh = _optional_float(value)
    if speed_kmh is None:
        return None
    return round(speed_kmh * KMH_TO_MPH, 2)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return round(float(value))


def _required(payload: dict[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value is None:
        raise GeotabMappingError(f"DeviceStatusInfo {key} is required")
    return value
