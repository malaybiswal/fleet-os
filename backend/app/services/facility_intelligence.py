"""Pure scoring functions for facility operational intelligence (TASK-036A).

All scores are 0-100. ``detention_risk`` is inverted (higher = worse); the
composite ``operational_score`` folds it back in as ``100 - risk``.
"""

from __future__ import annotations

# Hours of free time before a visit is considered to have hit detention.
# Matches the seed convention: detention_pay = (dwell_hours - 2) * 75.
DETENTION_FREE_HOURS = 2.0
# Average excess dwell (beyond free time) treated as maximum-severity detention.
DETENTION_MAX_EXCESS_HOURS = 4.0
DETENTION_FREQUENCY_WEIGHT = 60.0
DETENTION_MAGNITUDE_WEIGHT = 40.0

# Loading may start this many minutes after the appointment and still count on-time.
APPOINTMENT_GRACE_MINUTES = 30

# Composite weights.
DWELL_WEIGHT = 0.40
APPOINTMENT_WEIGHT = 0.30
DETENTION_WEIGHT = 0.30

# Detention risk bands — the contract consumed by facility risk badges (TASK-036B).
RISK_BAND_LOW_MAX = 35.0
RISK_BAND_HIGH_MIN = 65.0

CONFIDENCE_MEDIUM_MIN_VISITS = 3
CONFIDENCE_HIGH_MIN_VISITS = 10


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def dwell_score(avg_dwell_hours: float) -> float:
    return _clamp(100.0 - avg_dwell_hours * 10.0)


def appointment_reliability(appt_visits: int, appt_on_time: int) -> float | None:
    if appt_visits <= 0:
        return None
    return _clamp(100.0 * appt_on_time / appt_visits)


def detention_risk(
    visit_count: int,
    detention_visits: int,
    avg_excess_dwell_hours: float,
) -> float | None:
    if visit_count <= 0:
        return None
    frequency = detention_visits / visit_count
    magnitude = min(1.0, max(0.0, avg_excess_dwell_hours) / DETENTION_MAX_EXCESS_HOURS)
    return _clamp(
        round(
            DETENTION_FREQUENCY_WEIGHT * frequency
            + DETENTION_MAGNITUDE_WEIGHT * magnitude
        )
    )


def detention_risk_band(risk_score: float | None) -> str | None:
    if risk_score is None:
        return None
    if risk_score < RISK_BAND_LOW_MAX:
        return "low"
    if risk_score <= RISK_BAND_HIGH_MIN:
        return "medium"
    return "high"


def operational_score(
    dwell: float | None,
    reliability: float | None,
    risk: float | None,
) -> float | None:
    components = [
        (DWELL_WEIGHT, dwell),
        (APPOINTMENT_WEIGHT, reliability),
        (DETENTION_WEIGHT, 100.0 - risk if risk is not None else None),
    ]
    present = [(weight, value) for weight, value in components if value is not None]
    if not present:
        return None
    total_weight = sum(weight for weight, _ in present)
    weighted = sum(weight * value for weight, value in present) / total_weight
    return _clamp(round(weighted))


def confidence(visit_count: int) -> str:
    if visit_count >= CONFIDENCE_HIGH_MIN_VISITS:
        return "high"
    if visit_count >= CONFIDENCE_MEDIUM_MIN_VISITS:
        return "medium"
    return "low"
