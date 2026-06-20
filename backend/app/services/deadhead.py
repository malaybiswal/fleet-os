from math import asin, cos, radians, sin, sqrt


EARTH_RADIUS_MILES = 3958.8
DEADHEAD_SOURCE_HAVERSINE = "haversine"
DEADHEAD_SOURCE_STORED_FALLBACK = "stored-fallback"


def haversine_miles(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    )
    c = 2 * asin(sqrt(a))
    return round(EARTH_RADIUS_MILES * c, 1)


def truck_deadhead_miles(position: object, load: object) -> tuple[float, str]:
    truck_lat = _float_or_none(getattr(position, "latitude", None))
    truck_lon = _float_or_none(getattr(position, "longitude", None))
    origin_lat = _float_or_none(getattr(load, "origin_lat", None))
    origin_lon = _float_or_none(getattr(load, "origin_lon", None))

    if None not in {truck_lat, truck_lon, origin_lat, origin_lon}:
        return (
            haversine_miles(
                truck_lat,
                truck_lon,
                origin_lat,
                origin_lon,
            ),
            DEADHEAD_SOURCE_HAVERSINE,
        )

    return (
        max(0.0, _float_or_none(getattr(load, "deadhead_miles", None)) or 0.0),
        DEADHEAD_SOURCE_STORED_FALLBACK,
    )


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
