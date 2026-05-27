from decimal import Decimal

import pytest

from app.services.operational_status import (
    OperationalStatus,
    derive_operational_status,
)


@pytest.mark.parametrize(
    ("speed_mph", "expected"),
    [
        (0, OperationalStatus.STOPPED.value),
        (Decimal("0.00"), OperationalStatus.STOPPED.value),
        (Decimal("0.01"), OperationalStatus.IDLE.value),
        (5, OperationalStatus.IDLE.value),
        (Decimal("5.01"), OperationalStatus.SLOW.value),
        (20, OperationalStatus.SLOW.value),
        (Decimal("20.01"), OperationalStatus.MOVING.value),
        (55, OperationalStatus.MOVING.value),
    ],
)
def test_derive_operational_status_from_speed(speed_mph, expected):
    assert derive_operational_status(speed_mph=speed_mph) == expected


@pytest.mark.parametrize("speed_mph", [0, 3, 10, 55, None])
def test_derive_operational_status_maintenance_override(speed_mph):
    assert (
        derive_operational_status(
            speed_mph=speed_mph,
            reported_status="maintenance",
        )
        == OperationalStatus.MAINTENANCE.value
    )


def test_derive_operational_status_preserves_current_status_when_speed_missing():
    assert (
        derive_operational_status(
            speed_mph=None,
            current_status="slow",
        )
        == OperationalStatus.SLOW.value
    )


def test_derive_operational_status_defaults_to_stopped_when_speed_and_status_missing():
    assert (
        derive_operational_status(
            speed_mph=None,
            current_status="active",
        )
        == OperationalStatus.STOPPED.value
    )
