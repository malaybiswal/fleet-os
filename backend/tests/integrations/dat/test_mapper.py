import pytest

from app.integrations.dat.mapper import DatMappingError, map_dat_load_to_normalized


def test_map_dat_load_to_normalized():
    normalized = map_dat_load_to_normalized(
        {
            "id": "DAT-123",
            "origin": {"city": "Dallas", "state": "TX", "lat": 32.7, "lon": -96.8},
            "destination": {"city": "Houston", "state": "TX"},
            "equipment": "Dry Van",
            "rateUsd": "1250",
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


def test_map_nested_dat_load_shape_to_normalized():
    normalized = map_dat_load_to_normalized(
        {
            "postingId": "DAT-NESTED-1",
            "pickup": {
                "location": {
                    "city": "Fort Worth",
                    "state": "TX",
                    "latitude": 32.8,
                    "longitude": -97.3,
                },
                "earliest": "2026-06-27T14:00:00Z",
            },
            "delivery": {
                "location": {"city": "Phoenix", "state": "AZ"},
                "latest": "2026-06-28T19:00:00Z",
            },
            "equipment": {"type": "Reefer"},
            "rate": {"amount": 2600},
            "trip": {"loadedMiles": 970},
            "deadhead": {"miles": 34},
            "company": {"name": "DAT Broker Co"},
            "weight": {"lbs": 42000},
            "commodity": {"name": "Produce"},
        },
        fleet_id=8,
    )

    assert normalized.source_event_id == "DAT-NESTED-1"
    assert normalized.origin == "Fort Worth, TX"
    assert normalized.destination == "Phoenix, AZ"
    assert normalized.equipment_type == "Reefer"
    assert normalized.gross_revenue == 2600
    assert normalized.total_miles == 970
    assert normalized.deadhead_miles == 34
    assert normalized.broker_name == "DAT Broker Co"
    assert normalized.weight == 42000
    assert normalized.commodity == "Produce"


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
