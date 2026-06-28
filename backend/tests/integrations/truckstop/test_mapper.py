import pytest

from app.integrations.truckstop.mapper import (
    TruckstopMappingError,
    map_truckstop_load_to_normalized,
)


def test_map_truckstop_load_to_normalized():
    normalized = map_truckstop_load_to_normalized(
        {
            "ID": "TS-123",
            "OriginCity": "Dallas",
            "OriginState": "TX",
            "OriginLatitude": "32.7",
            "OriginLongitude": "-96.8",
            "DestinationCity": "Houston",
            "DestinationState": "TX",
            "Equipment": "V",
            "Payment": "$1,250.00",
            "Miles": "245",
            "OriginDistance": "20",
            "CompanyName": "Truckstop Demo Brokerage",
            "PickUpDate": "11/11/24",
            "Weight": "42877",
        },
        fleet_id=8,
    )

    assert normalized.fleet_id == 8
    assert normalized.source == "truckstop"
    assert normalized.source_event_id == "TS-123"
    assert normalized.origin == "Dallas, TX"
    assert normalized.destination == "Houston, TX"
    assert normalized.equipment_type == "Dry Van"
    assert normalized.gross_revenue == 1250
    assert normalized.total_miles == 245
    assert normalized.deadhead_miles == 20
    assert normalized.broker_name == "Truckstop Demo Brokerage"
    assert normalized.pickup_time is not None
    assert normalized.weight == 42877


def test_map_nested_truckstop_load_shape_to_normalized():
    normalized = map_truckstop_load_to_normalized(
        {
            "LoadId": "TS-NESTED-1",
            "origin": {"city": "Fort Worth", "state": "TX", "lat": 32.8, "lon": -97.3},
            "destination": {"city": "Phoenix", "state": "AZ"},
            "EquipmentType": "Reefer",
            "PaymentAmount": 2600,
            "Mileage": 970,
            "OriginDistance": 34,
            "CompanyName": "Truckstop Broker Co",
            "DeliveryDate": "2026-06-28",
        },
        fleet_id=8,
    )

    assert normalized.source_event_id == "TS-NESTED-1"
    assert normalized.origin == "Fort Worth, TX"
    assert normalized.destination == "Phoenix, AZ"
    assert normalized.equipment_type == "Reefer"
    assert normalized.gross_revenue == 2600
    assert normalized.total_miles == 970
    assert normalized.deadhead_miles == 34
    assert normalized.broker_name == "Truckstop Broker Co"
    assert normalized.delivery_time is not None


def test_map_truckstop_load_rejects_malformed_payload():
    with pytest.raises(TruckstopMappingError):
        map_truckstop_load_to_normalized(
            {
                "ID": "TS-BAD",
                "OriginCity": "Dallas",
                "OriginState": "TX",
                "DestinationCity": "Houston",
                "DestinationState": "TX",
                "Payment": 0,
                "Miles": 245,
            },
            fleet_id=8,
        )
