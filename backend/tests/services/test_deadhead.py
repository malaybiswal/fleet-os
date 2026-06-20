from decimal import Decimal
from types import SimpleNamespace

from app.services.deadhead import (
    DEADHEAD_SOURCE_HAVERSINE,
    DEADHEAD_SOURCE_STORED_FALLBACK,
    haversine_miles,
    truck_deadhead_miles,
)


def test_haversine_miles_matches_known_texas_distance():
    miles = haversine_miles(32.7767, -96.7970, 29.7604, -95.3698)

    assert 224 <= miles <= 227


def test_truck_deadhead_uses_coordinates_when_available():
    position = SimpleNamespace(latitude=32.7767, longitude=-96.7970)
    load = SimpleNamespace(
        origin_lat=Decimal("29.760400"),
        origin_lon=Decimal("-95.369800"),
        deadhead_miles=Decimal("20"),
    )

    miles, source = truck_deadhead_miles(position, load)

    assert 224 <= miles <= 227
    assert source == DEADHEAD_SOURCE_HAVERSINE


def test_truck_deadhead_falls_back_to_stored_deadhead_when_coordinates_missing():
    position = SimpleNamespace(latitude=None, longitude=None)
    load = SimpleNamespace(
        origin_lat=Decimal("29.760400"),
        origin_lon=Decimal("-95.369800"),
        deadhead_miles=Decimal("42"),
    )

    miles, source = truck_deadhead_miles(position, load)

    assert miles == 42
    assert source == DEADHEAD_SOURCE_STORED_FALLBACK
