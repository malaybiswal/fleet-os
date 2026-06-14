from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Iterable, Protocol


class OperationalStatus(StrEnum):
    STOPPED = "stopped"
    IDLE = "idle"
    SLOW = "slow"
    MOVING = "moving"
    MAINTENANCE = "maintenance"


# ``"active"`` is a legacy status string that predates the OperationalStatus enum.
# It is retained here defensively for any old DB rows, but nothing in the system
# should store it anymore: ``_normalize`` maps ``"active"`` -> ``MOVING`` so all
# status derivation funnels through real enum values.
OPERATIONALLY_ACTIVE_STATUSES = (
    "active",
    OperationalStatus.MOVING.value,
    OperationalStatus.SLOW.value,
)


def derive_operational_status(
    speed_mph: Decimal | float | int | None,
    reported_status: str | None = None,
    current_status: str | None = None,
) -> str:
    if _normalize(reported_status) == OperationalStatus.MAINTENANCE:
        return OperationalStatus.MAINTENANCE.value

    if speed_mph is None:
        normalized_current_status = _normalize(current_status)
        if normalized_current_status is not None:
            return normalized_current_status.value
        return OperationalStatus.STOPPED.value

    speed = Decimal(str(speed_mph))

    if speed <= 0:
        return OperationalStatus.STOPPED.value
    if speed <= 5:
        return OperationalStatus.IDLE.value
    if speed <= 20:
        return OperationalStatus.SLOW.value

    return OperationalStatus.MOVING.value


class _StationaryEvent(Protocol):
    speed: Decimal | float | int | None
    timestamp: datetime


def stationary_minutes(
    events_newest_first: Iterable[_StationaryEvent],
    as_of: datetime,
) -> float:
    """Minutes the truck has been continuously non-moving (<=5 mph) as of ``as_of``.

    Walks the events newest -> oldest; the first SLOW/MOVING event (>5 mph) stops
    the clock. The window is bounded by the caller's query, so an all-stationary
    window yields the time back to the oldest event provided.
    """
    earliest = as_of
    for event in events_newest_first:
        status = derive_operational_status(speed_mph=event.speed)
        if status in (OperationalStatus.SLOW, OperationalStatus.MOVING):
            break
        earliest = event.timestamp
    return (as_of - earliest).total_seconds() / 60


def _normalize(status: str | None) -> OperationalStatus | None:
    if status is None:
        return None

    normalized = status.strip().lower()

    # Legacy alias: "active" was used before the enum existed; treat it as MOVING.
    if normalized == "active":
        return OperationalStatus.MOVING

    try:
        return OperationalStatus(normalized)
    except ValueError:
        return None
