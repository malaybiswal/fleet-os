from datetime import datetime
from typing import Any

from app.ingestion.normalized_events import NormalizedLoadObject


class DatMappingError(ValueError):
    pass


def map_dat_load_to_normalized(
    payload: dict[str, Any],
    *,
    fleet_id: int,
) -> NormalizedLoadObject:
    try:
        source_event_id = str(payload.get("id") or payload["loadId"])
        origin = _format_place(payload.get("origin"))
        destination = _format_place(payload.get("destination"))
        gross_revenue = _number(payload.get("rate") or payload.get("rateUsd") or payload.get("payout"))
        total_miles = _number(payload.get("miles") or payload.get("totalMiles"))
    except (KeyError, TypeError, ValueError) as exc:
        raise DatMappingError(f"Malformed DAT load posting: {exc}") from exc

    return NormalizedLoadObject(
        fleet_id=fleet_id,
        source="dat",
        source_event_id=source_event_id,
        origin=origin,
        destination=destination,
        origin_lat=_optional_number((payload.get("origin") or {}).get("lat")),
        origin_lon=_optional_number((payload.get("origin") or {}).get("lon")),
        equipment_type=payload.get("equipment") or payload.get("equipmentType"),
        gross_revenue=gross_revenue,
        total_miles=total_miles,
        deadhead_miles=_optional_number(payload.get("deadheadMiles")) or 0,
        broker_name=(payload.get("broker") or {}).get("name") or payload.get("brokerName"),
        pickup_time=_optional_datetime(payload.get("pickupTime")),
        delivery_time=_optional_datetime(payload.get("deliveryTime")),
        weight=_optional_number(payload.get("weight")),
        commodity=payload.get("commodity"),
        raw_payload=payload,
    )


def _format_place(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        city = value.get("city")
        state = value.get("state")
        parts = [str(part).strip() for part in (city, state) if part]
        if parts:
            return ", ".join(parts)
    raise DatMappingError("origin and destination are required")


def _number(value: Any) -> float:
    number = float(value)
    if number <= 0:
        raise DatMappingError("rate and miles must be positive")
    return number


def _optional_number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
