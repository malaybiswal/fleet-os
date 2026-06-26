import pytest

from app.integrations.dat.mapper import DatMappingError, map_dat_load_to_normalized


def test_map_dat_load_to_normalized():
    normalized = map_dat_load_to_normalized(
        {
            "id": "DAT-123",
            "origin": {"city": "Dallas", "state": "TX", "lat": 32.7, "lon": -96.8},
            "destination": {"city": "Houston", "state": "TX"},
            "equipment": "Dry Van",
            "rate": "1250",
            "miles": "245",
            "deadheadMiles": "20",
            "broker": {"name": "DAT Demo Brokerage"},
            "pickupTime": "2026-06-27T14:00:00Z",
        },
        fleet_id=8,
    )

    assert normalized.fleet_id == 8
    assert normalized.source == "dat"
    assert normalized.source_event_id == "DAT-123"
    assert normalized.origin == "Dallas, TX"
    assert normalized.destination == "Houston, TX"
    assert normalized.gross_revenue == 1250
    assert normalized.total_miles == 245
    assert normalized.deadhead_miles == 20
    assert normalized.broker_name == "DAT Demo Brokerage"
    assert normalized.pickup_time is not None


def test_map_dat_load_rejects_malformed_payload():
    with pytest.raises(DatMappingError):
        map_dat_load_to_normalized(
            {
                "id": "DAT-BAD",
                "origin": {"city": "Dallas", "state": "TX"},
                "destination": {"city": "Houston", "state": "TX"},
                "rate": 0,
                "miles": 245,
            },
            fleet_id=8,
        )
