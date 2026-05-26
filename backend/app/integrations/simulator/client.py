from datetime import datetime, timezone
from math import atan2, cos, degrees, radians, sin
from random import choice, uniform


ROUTES = {
    "SIM-001": [
        ("Dallas, TX", 32.7767, -96.7970),
        ("Waco, TX", 31.5493, -97.1467),
        ("Austin, TX", 30.2672, -97.7431),
        ("San Antonio, TX", 29.4252, -98.4946),
    ],
    "SIM-002": [
        ("Houston, TX", 29.7604, -95.3698),
        ("Beaumont, TX", 30.0802, -94.1266),
        ("Lake Charles, LA", 30.2266, -93.2174),
        ("Baton Rouge, LA", 30.4515, -91.1871),
    ],
    "SIM-003": [
        ("Laredo, TX", 27.5306, -99.4803),
        ("San Antonio, TX", 29.4252, -98.4946),
        ("Austin, TX", 30.2672, -97.7431),
        ("Dallas, TX", 32.7767, -96.7970),
    ],
    "SIM-004": [
        ("El Paso, TX", 31.7619, -106.4850),
        ("Midland, TX", 31.9973, -102.0779),
        ("Abilene, TX", 32.4487, -99.7331),
        ("Fort Worth, TX", 32.7555, -97.3308),
    ],
    "SIM-005": [
        ("Oklahoma City, OK", 35.4676, -97.5164),
        ("Wichita Falls, TX", 33.9137, -98.4934),
        ("Fort Worth, TX", 32.7555, -97.3308),
        ("Dallas, TX", 32.7767, -96.7970),
    ],
}


def _calculate_heading(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> int:
    start_lat_rad = radians(start_lat)
    end_lat_rad = radians(end_lat)
    delta_lon_rad = radians(end_lon - start_lon)

    x = sin(delta_lon_rad) * cos(end_lat_rad)
    y = cos(start_lat_rad) * sin(end_lat_rad) - (
        sin(start_lat_rad) * cos(end_lat_rad) * cos(delta_lon_rad)
    )

    heading = (degrees(atan2(x, y)) + 360) % 360

    return round(heading)


def _interpolate(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    progress: float,
) -> tuple[float, float]:
    latitude = start_lat + ((end_lat - start_lat) * progress)
    longitude = start_lon + ((end_lon - start_lon) * progress)

    return latitude, longitude


def _build_payload_for_truck(
    truck_id: str,
    route: list[tuple[str, float, float]],
    route_offset: int,
) -> dict:
    segment_count = len(route) - 1
    segment_index = route_offset % segment_count
    next_segment_index = segment_index + 1

    start_name, start_lat, start_lon = route[segment_index]
    end_name, end_lat, end_lon = route[next_segment_index]

    progress = uniform(0.15, 0.85)

    latitude, longitude = _interpolate(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        progress=progress,
    )

    status = choice(["active", "active", "active", "idle", "maintenance"])

    if status == "active":
        speed_mph = round(uniform(45, 72), 2)
    elif status == "idle":
        speed_mph = round(uniform(0, 5), 2)
    else:
        speed_mph = 0

    heading = (
        _calculate_heading(start_lat, start_lon, end_lat, end_lon)
        if status == "active"
        else 0
    )

    return {
        "vehicle_id": truck_id,
        "fleet_id": 17,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": {
            "description": f"{start_name} → {end_name}",
            "lat": latitude,
            "lon": longitude,
        },
        "speed_mph": speed_mph,
        "heading": heading,
        "status": status,
    }


def fetch_simulated_vehicle_payloads() -> list[dict]:
    payloads = []

    for route_offset, (truck_id, route) in enumerate(ROUTES.items()):
        payloads.append(
            _build_payload_for_truck(
                truck_id=truck_id,
                route=route,
                route_offset=route_offset,
            )
        )

    return payloads