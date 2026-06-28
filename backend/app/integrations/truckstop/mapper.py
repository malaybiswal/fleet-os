from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from app.ingestion.normalized_events import NormalizedLoadObject


class TruckstopMappingError(ValueError):
    pass


def map_truckstop_load_to_normalized(
    payload: dict[str, Any],
    *,
    fleet_id: int,
) -> NormalizedLoadObject:
    try:
        source_event_value = _first_value(payload, "ID", "LoadId", "LoadID", "id")
        if source_event_value in (None, ""):
            raise TruckstopMappingError("Truckstop load id is required")
        source_event_id = str(source_event_value)
        origin = _format_place(
            _first_value(payload, "OriginCity", "origin.city"),
            _first_value(payload, "OriginState", "origin.state"),
            "origin",
        )
        destination = _format_place(
            _first_value(payload, "DestinationCity", "destination.city"),
            _first_value(payload, "DestinationState", "destination.state"),
            "destination",
        )
        gross_revenue = _number(
            _first_value(payload, "Payment", "PaymentAmount", "payment.amount", "rate")
        )
        total_miles = _number(
            _first_value(payload, "Miles", "Mileage", "Distance", "distance.miles")
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise TruckstopMappingError(f"Malformed Truckstop load posting: {exc}") from exc

    return NormalizedLoadObject(
        fleet_id=fleet_id,
        source="truckstop",
        source_event_id=source_event_id,
        origin=origin,
        destination=destination,
        origin_lat=_optional_number(_first_value(payload, "OriginLatitude", "origin.lat")),
        origin_lon=_optional_number(_first_value(payload, "OriginLongitude", "origin.lon")),
        equipment_type=_format_equipment(
            _first_value(payload, "EquipmentType", "Equipment", "equipment.type")
        ),
        gross_revenue=gross_revenue,
        total_miles=total_miles,
        deadhead_miles=_optional_number(
            _first_value(payload, "OriginDistance", "deadheadMiles")
        )
        or 0,
        broker_name=_first_value(payload, "CompanyName", "broker.name", "brokerName"),
        pickup_time=_optional_datetime(
            _first_value(payload, "PickupDate", "PickUpDate", "pickupDate"),
            _first_value(payload, "PickupTime", "PickUpTime", "pickupTime"),
        ),
        delivery_time=_optional_datetime(
            _first_value(payload, "DeliveryDate", "deliveryDate"),
            _first_value(payload, "DeliveryTime", "deliveryTime"),
        ),
        weight=_optional_number(_first_value(payload, "Weight", "weight")),
        commodity=_first_value(payload, "Commodity", "commodity"),
        raw_payload=payload,
    )


def _format_place(city_value: Any, state_value: Any, field_name: str) -> str:
    city = str(city_value).strip() if city_value not in (None, "") else ""
    state = str(state_value).strip() if state_value not in (None, "") else ""
    parts = [part for part in (city, state) if part]
    if parts:
        return ", ".join(parts)
    raise TruckstopMappingError(f"{field_name} is required")


def _format_equipment(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        nested = _first_value(value, "type", "code", "name", "description")
        return _format_equipment(nested)
    normalized = str(value).strip()
    return {
        "V": "Dry Van",
        "R": "Reefer",
        "F": "Flatbed",
        "PO": "Power Only",
    }.get(normalized.upper(), normalized)


def _number(value: Any) -> float:
    number = _parse_number(value)
    if number <= 0:
        raise TruckstopMappingError("rate and miles must be positive")
    return number


def _optional_number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return _parse_number(value)


def _parse_number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^0-9.\-]", "", str(value))
    return float(cleaned)


def _optional_datetime(date_value: Any, time_value: Any = None) -> datetime | None:
    if date_value in (None, ""):
        return None
    raw = str(date_value).strip()
    if time_value not in (None, ""):
        raw = f"{raw} {str(time_value).strip()}"
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%y %H:%M",
        "%m/%d/%y",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
    ):
        try:
            return datetime.strptime(raw.replace("Z", "+0000"), fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def _first_value(payload: Any, *paths: str) -> Any:
    for path in paths:
        value = _dig(payload, path)
        if value not in (None, ""):
            return value
    return None


def _dig(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current
