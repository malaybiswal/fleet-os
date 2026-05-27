from decimal import Decimal
from enum import StrEnum


class OperationalStatus(StrEnum):
    STOPPED = "stopped"
    IDLE = "idle"
    SLOW = "slow"
    MOVING = "moving"
    MAINTENANCE = "maintenance"


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


def _normalize(status: str | None) -> OperationalStatus | None:
    if status is None:
        return None

    try:
        return OperationalStatus(status.strip().lower())
    except ValueError:
        return None
