from datetime import timezone

import pytest

from app.integrations.geotab.mapper import (
    GeotabMappingError,
    map_device_status_info_to_event,
)
from app.services.operational_status import OperationalStatus


def test_map_device_status_info_to_event_converts_geotab_payload():
    payload = {
        "device": {"id": "b123"},
        "dateTime": "2026-05-30T15:45:00Z",
        "latitude": 32.7767,
        "longitude": -96.797,
        "speed": 100,
        "bearing": 182.4,
    }

    event = map_device_status_info_to_event(payload, fleet_id=17)

    assert event.fleet_id == 17
    assert event.truck_id == "GEOTAB-17-b123"
    assert event.timestamp.tzinfo == timezone.utc
    assert event.latitude == 32.7767
    assert event.longitude == -96.797
    assert event.speed_mph == 62.14
    assert event.heading == 182
    assert event.status == OperationalStatus.MOVING.value
    assert event.source == "geotab"
    assert event.source_event_id == "geotab:b123:2026-05-30T15:45:00+00:00"
    assert event.raw_payload == payload


@pytest.mark.parametrize(
    ("speed_kmh", "expected_status"),
    [
        (0, OperationalStatus.STOPPED.value),
        (5, OperationalStatus.IDLE.value),
        (40, OperationalStatus.MOVING.value),
        (32, OperationalStatus.SLOW.value),
    ],
)
def test_map_device_status_info_uses_shared_operational_status_rules(
    speed_kmh,
    expected_status,
):
    payload = {
        "device": {"id": "b124"},
        "dateTime": "2026-05-30T15:45:00Z",
        "speed": speed_kmh,
    }

    event = map_device_status_info_to_event(payload, fleet_id=17)

    assert event.status == expected_status


def test_map_device_status_info_requires_device_id():
    with pytest.raises(GeotabMappingError):
        map_device_status_info_to_event(
            {
                "device": {},
                "dateTime": "2026-05-30T15:45:00Z",
            },
            fleet_id=17,
        )
