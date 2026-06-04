from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.services.operational_status import (
    OperationalStatus,
    derive_operational_status,
    stationary_minutes,
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


# ---------------------------------------------------------------------------
# stationary_minutes
# ---------------------------------------------------------------------------

@dataclass
class _Event:
    speed: Decimal | float | None
    timestamp: datetime


def _ts(minutes_ago: float) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)


def test_stationary_minutes_empty_events_returns_zero():
    assert stationary_minutes([], datetime.now(timezone.utc)) == 0.0


def test_stationary_minutes_single_stopped_event():
    as_of = datetime.now(timezone.utc)
    event = _Event(speed=Decimal("0"), timestamp=as_of - timedelta(minutes=30))
    assert stationary_minutes([event], as_of) == pytest.approx(30.0, abs=0.1)


def test_stationary_minutes_all_stationary_uses_oldest_event():
    as_of = datetime.now(timezone.utc)
    events = [
        _Event(speed=Decimal("0"), timestamp=as_of - timedelta(minutes=10)),
        _Event(speed=Decimal("3"), timestamp=as_of - timedelta(minutes=20)),
        _Event(speed=Decimal("0"), timestamp=as_of - timedelta(minutes=60)),
    ]
    assert stationary_minutes(events, as_of) == pytest.approx(60.0, abs=0.1)


def test_stationary_minutes_moving_event_stops_clock():
    as_of = datetime.now(timezone.utc)
    events = [
        _Event(speed=Decimal("0"),  timestamp=as_of - timedelta(minutes=10)),
        _Event(speed=Decimal("0"),  timestamp=as_of - timedelta(minutes=20)),
        _Event(speed=Decimal("65"), timestamp=as_of - timedelta(minutes=30)),  # moving
        _Event(speed=Decimal("0"),  timestamp=as_of - timedelta(minutes=90)),
    ]
    assert stationary_minutes(events, as_of) == pytest.approx(20.0, abs=0.1)


def test_stationary_minutes_slow_event_also_stops_clock():
    as_of = datetime.now(timezone.utc)
    events = [
        _Event(speed=Decimal("0"),  timestamp=as_of - timedelta(minutes=15)),
        _Event(speed=Decimal("12"), timestamp=as_of - timedelta(minutes=30)),  # slow
        _Event(speed=Decimal("0"),  timestamp=as_of - timedelta(minutes=90)),
    ]
    assert stationary_minutes(events, as_of) == pytest.approx(15.0, abs=0.1)


def test_stationary_minutes_idle_speed_counts_as_stationary():
    """1–5 mph is IDLE, which is stationary for duration purposes."""
    as_of = datetime.now(timezone.utc)
    events = [
        _Event(speed=Decimal("3"), timestamp=as_of - timedelta(minutes=20)),
        _Event(speed=Decimal("2"), timestamp=as_of - timedelta(minutes=45)),
    ]
    assert stationary_minutes(events, as_of) == pytest.approx(45.0, abs=0.1)


def test_stationary_minutes_none_speed_counts_as_stationary():
    as_of = datetime.now(timezone.utc)
    events = [_Event(speed=None, timestamp=as_of - timedelta(minutes=35))]
    assert stationary_minutes(events, as_of) == pytest.approx(35.0, abs=0.1)


def test_stationary_minutes_moving_at_newest_event_returns_zero():
    as_of = datetime.now(timezone.utc)
    events = [
        _Event(speed=Decimal("65"), timestamp=as_of - timedelta(minutes=5)),
        _Event(speed=Decimal("0"),  timestamp=as_of - timedelta(minutes=60)),
    ]
    assert stationary_minutes(events, as_of) == 0.0
