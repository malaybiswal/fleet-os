"""
Pure mapping functions: Motive API raw dict → internal Pydantic schema.

No DB access, no side effects. Each function receives a single raw record dict
as returned by the Motive API and returns the corresponding internal schema.

Motive API shape reference (v2):
  Vehicle:  { id, number, status, current_location: {lat, lon, description}, last_location_time }
  User:     { id, username, first_name, last_name, status, role }
  Location: { id, vehicle: {id, number}, located_at, lat, lon, speed, fuel_level, engine_hours }
"""

from datetime import datetime, timezone

from app.schemas.driver import DriverCreate
from app.schemas.telemetry_event import TelemetryEventCreate
from app.schemas.truck import TruckCreate

_MOTIVE_TO_INTERNAL_STATUS = {
    "active": "active",
    "inactive": "idle",
    "deactivated": "maintenance",
}

_MOTIVE_DRIVER_STATUS = {
    "active": "available",
    "inactive": "off_duty",
}


def map_vehicle(raw: dict) -> tuple[TruckCreate, str]:
    """
    Returns (TruckCreate, provider_id).
    provider_id is the Motive vehicle integer id cast to str.
    truck_id is derived from the vehicle number when present,
    otherwise falls back to "motive-{id}".
    """
    vehicle_id = str(raw["id"])
    truck_id = str(raw.get("number") or f"motive-{vehicle_id}")
    status = _MOTIVE_TO_INTERNAL_STATUS.get(raw.get("status", ""), "idle")

    loc = raw.get("current_location") or {}
    lat = loc.get("lat")
    lon = loc.get("lon")
    location_desc = loc.get("description")

    last_seen_raw = raw.get("last_location_time")
    last_seen_at = _parse_dt(last_seen_raw) if last_seen_raw else None

    return (
        TruckCreate(
            truck_id=truck_id,
            status=status,
            current_location=location_desc,
            current_lat=lat,
            current_lon=lon,
            last_seen_at=last_seen_at,
        ),
        vehicle_id,
    )


def map_driver(raw: dict) -> tuple[DriverCreate, str]:
    """
    Returns (DriverCreate, provider_id).
    driver_id is set to "motive-{id}" so it never collides with manual records.
    """
    user_id = str(raw["id"])
    first = raw.get("first_name", "")
    last = raw.get("last_name", "")
    name = f"{first} {last}".strip() or raw.get("username", f"motive-{user_id}")
    status = _MOTIVE_DRIVER_STATUS.get(raw.get("status", ""), "off_duty")

    return (
        DriverCreate(
            driver_id=f"motive-{user_id}",
            name=name,
            status=status,
        ),
        user_id,
    )


def map_location(raw: dict, truck_id: str) -> tuple[TelemetryEventCreate, str]:
    """
    Returns (TelemetryEventCreate, provider_id).
    truck_id must be the internal truck_id already resolved by the ingestion service.
    provider_id is the Motive location id (string).
    """
    location_id = str(raw["id"])
    timestamp = _parse_dt(raw["located_at"])

    # Motive speed is in mph; store as-is (our schema is unitless Decimal)
    speed = raw.get("speed")
    fuel_level = raw.get("fuel_level")

    return (
        TelemetryEventCreate(
            truck_id=truck_id,
            timestamp=timestamp,
            speed=speed,
            gps_lat=raw.get("lat"),
            gps_lon=raw.get("lon"),
            fuel_level=fuel_level,
        ),
        location_id,
    )


def _parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
