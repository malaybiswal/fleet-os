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
        source_event_value = _first_value(
            payload, "id", "loadId", "load_id", "postingId", "posting_id"
        )
        if source_event_value in (None, ""):
            raise DatMappingError("DAT load id is required")
        source_event_id = str(source_event_value)
        origin_payload = _first_value(
            payload,
            "origin",
            "pickupLocation",
            "pickup.location",
            "pickup",
            "from",
        )
        destination_payload = _first_value(
            payload,
            "destination",
            "deliveryLocation",
            "delivery.location",
            "delivery",
            "dropoff",
            "to",
        )
        origin = _format_place(origin_payload)
        destination = _format_place(destination_payload)
        gross_revenue = _number(
            _first_value(
                payload,
                "rateUsd",
                "payout",
                "spotRate.amount",
                "rate.amount",
                "pricing.rate",
                "payment.amount",
                "rate",
            )
        )
        total_miles = _number(
            _first_value(
                payload,
                "miles",
                "totalMiles",
                "tripMiles",
                "loadedMiles",
                "trip.loadedMiles",
                "distance.miles",
                "route.miles",
            )
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DatMappingError(f"Malformed DAT load posting: {exc}") from exc

    return NormalizedLoadObject(
        fleet_id=fleet_id,
        source="dat",
        source_event_id=source_event_id,
        origin=origin,
        destination=destination,
        origin_lat=_optional_number(_first_value(origin_payload, "lat", "latitude")),
        origin_lon=_optional_number(_first_value(origin_payload, "lon", "lng", "longitude")),
        equipment_type=_format_equipment(
            _first_value(payload, "equipment", "equipmentType", "trailerType")
        ),
        gross_revenue=gross_revenue,
        total_miles=total_miles,
        deadhead_miles=_optional_number(
            _first_value(payload, "deadheadMiles", "deadhead.miles")
        ) or 0,
        broker_name=_first_value(
            payload,
            "broker.name",
            "brokerName",
            "company.name",
            "poster.company.name",
            "customer.name",
        ),
        pickup_time=_optional_datetime(
            _first_value(
                payload,
                "pickupTime",
                "pickupDateTime",
                "pickup.dateTime",
                "pickup.earliest",
                "availability.earliestPickup",
            )
        ),
        delivery_time=_optional_datetime(
            _first_value(
                payload,
                "deliveryTime",
                "deliveryDateTime",
                "delivery.dateTime",
                "delivery.latest",
                "availability.latestDelivery",
            )
        ),
        weight=_optional_number(_first_value(payload, "weightPounds", "weight.lbs", "weight")),
        commodity=_first_value(payload, "commodity.name", "commodity"),
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


def _format_equipment(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        nested = _first_value(value, "type", "code", "name", "description")
        return str(nested) if nested not in (None, "") else None
    return str(value)


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
