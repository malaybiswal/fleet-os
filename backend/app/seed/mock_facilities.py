import math
from datetime import datetime, timedelta
from decimal import Decimal
import random

from app.schemas.facility import FacilityRiskSummary
from app.seed.types import DwellEventSeed, FacilitySeed, LoadSeed
from app.services import facility_intelligence as fi

DEMO_FACILITIES = (
    FacilitySeed("operations", "Houston Crossdock", "Houston", "TX", Decimal("29.7604"), Decimal("-95.3698"), "crossdock"),
    FacilitySeed("operations", "Denver West DC", "Denver", "CO", Decimal("39.7392"), Decimal("-104.9903"), "distribution_center"),
    FacilitySeed("refrigerated", "Dallas Mega Cold Storage", "Dallas", "TX", Decimal("32.7767"), Decimal("-96.7970"), "cold_storage"),
    FacilitySeed("operations", "Atlanta Reload Hub", "Atlanta", "GA", Decimal("33.7490"), Decimal("-84.3880"), "crossdock"),
    FacilitySeed("operations", "Oklahoma Pipe Yard", "Oklahoma City", "OK", Decimal("35.4676"), Decimal("-97.5164"), "yard"),
    FacilitySeed("operations", "Phoenix Grocery DC", "Phoenix", "AZ", Decimal("33.4484"), Decimal("-112.0740"), "distribution_center"),
)

# Primary demo visits, one per strategic demo load (kept for the load-evaluation demos).
DEMO_DWELL_SCENARIOS = (
    ("DEMO-LOAD-GOOD", "operations", "Houston Crossdock", "CH Robinson", 1.2, "Fast unload, reliable appointment."),
    ("DEMO-LOAD-HIGH-PAY-BAD", "operations", "Denver West DC", "Coyote", 3.8, "Long check-in and unload window."),
    ("DEMO-LOAD-HIGH-DWELL", "refrigerated", "Dallas Mega Cold Storage", "Cold Chain Logistics", 7.1, "High dwell risk facility for reefer freight."),
    ("DEMO-LOAD-STRONG-RELOAD", "operations", "Atlanta Reload Hub", "Uber Freight", 1.4, "Strong reload market and fast turn."),
    ("DEMO-LOAD-BAD-DEADHEAD", "operations", "Oklahoma Pipe Yard", "TQL", 2.6, "Deadhead-heavy lane with average dock time."),
    ("DEMO-LOAD-WEAK-BROKER", "operations", "Phoenix Grocery DC", "TQL Risk Desk", 5.4, "Weak broker communication and detention dispute risk."),
)

# Scripted visit history per facility: (dwell_hours, appointment_delay_minutes).
# The first visit is the primary DEMO_DWELL_SCENARIOS load; the rest get
# dedicated history loads. Tuned so the facility intelligence engine lands each
# facility in a deterministic operational-score band:
#   good (>75):       Houston Crossdock, Atlanta Reload Hub
#   medium (40-75):   Denver West DC, Oklahoma Pipe Yard
#   high risk (<40):  Dallas Mega Cold Storage, Phoenix Grocery DC
DEMO_FACILITY_VISIT_PLANS = {
    "Houston Crossdock": ((1.2, 10), (1.0, 5), (1.4, 15), (1.1, 0)),
    "Denver West DC": ((3.8, 45), (1.8, 10), (2.6, 20), (1.5, 25)),
    "Dallas Mega Cold Storage": ((7.1, 120), (6.5, 180), (7.8, 150)),
    "Atlanta Reload Hub": ((1.4, 10), (1.3, 20), (1.6, 5)),
    "Oklahoma Pipe Yard": ((2.6, 40), (3.2, 50), (2.0, 10), (2.4, 20)),
    "Phoenix Grocery DC": ((5.4, 90), (6.0, 120), (4.8, 25)),
}

_HISTORY_TRUCKS = (
    ("DEMO-TRUCK-001", "DEMO-DRIVER-001"),
    ("DEMO-TRUCK-002", "DEMO-DRIVER-002"),
    ("DEMO-TRUCK-003", "DEMO-DRIVER-006"),
    ("DEMO-TRUCK-004", "DEMO-DRIVER-003"),
    ("DEMO-TRUCK-005", "DEMO-DRIVER-004"),
    ("DEMO-TRUCK-006", "DEMO-DRIVER-005"),
)


def build_demo_facilities() -> tuple[FacilitySeed, ...]:
    return DEMO_FACILITIES


def _history_load_id(facility_index: int, visit_index: int) -> str:
    return f"DEMO-LOAD-FAC-{facility_index + 1}{visit_index}"


def build_demo_facility_history_loads(
    base_date: datetime,
    rng: random.Random,
) -> tuple[LoadSeed, ...]:
    """Delivered loads backing the extra (non-primary) facility visits."""
    loads: list[LoadSeed] = []
    for facility_index, (load_id, fleet_key, facility, broker, _, _) in enumerate(DEMO_DWELL_SCENARIOS):
        visits = DEMO_FACILITY_VISIT_PLANS[facility]
        for visit_index in range(1, len(visits)):
            truck_id, driver_id = _HISTORY_TRUCKS[facility_index % len(_HISTORY_TRUCKS)]
            miles = 420 + facility_index * 60 + visit_index * 35
            pickup_time = base_date - timedelta(days=3 * visit_index + facility_index, hours=14)
            loads.append(
                LoadSeed(
                    load_id=_history_load_id(facility_index, visit_index),
                    fleet_key=fleet_key,
                    truck_id=truck_id,
                    driver_id=driver_id,
                    scenario_key="facility_history",
                    broker_name=broker,
                    origin="Demo Origin",
                    destination=facility,
                    revenue=_money(miles * 2.4, rng),
                    miles=Decimal(str(miles)),
                    deadhead_miles=Decimal(str(40 + visit_index * 10)),
                    fuel_cost=_money((miles / 7.0) * 4.0, rng),
                    maintenance_reserve=_money(miles * 0.12, rng),
                    driver_cost=_money(miles * 0.72, rng),
                    tolls=_money(20 + facility_index * 5, rng),
                    pickup_time=pickup_time,
                    delivery_time=pickup_time + timedelta(hours=max(4, round(miles / 50))),
                    status="delivered",
                )
            )

    return tuple(loads)


def build_demo_dwell_events(
    base_date: datetime,
    rng: random.Random,
) -> tuple[DwellEventSeed, ...]:
    dwell_events: list[DwellEventSeed] = []
    for facility_index, (load_id, fleet_key, facility, broker, _, notes) in enumerate(DEMO_DWELL_SCENARIOS):
        for visit_index, (dwell_hours, delay_minutes) in enumerate(DEMO_FACILITY_VISIT_PLANS[facility]):
            if visit_index == 0:
                visit_load_id = load_id
                appointment_time = base_date + timedelta(hours=facility_index * 2)
            else:
                visit_load_id = _history_load_id(facility_index, visit_index)
                appointment_time = base_date - timedelta(
                    days=3 * visit_index + facility_index, hours=2
                )

            arrival_time = appointment_time - timedelta(minutes=15)
            loading_start = appointment_time + timedelta(minutes=delay_minutes)
            departure_time = arrival_time + timedelta(hours=dwell_hours)
            loading_end = min(
                loading_start + timedelta(hours=max(0.5, dwell_hours - 1.0)),
                departure_time - timedelta(minutes=10),
            )

            dwell_events.append(
                DwellEventSeed(
                    load_id=visit_load_id,
                    fleet_key=fleet_key,
                    facility_name=facility,
                    broker_name=broker,
                    appointment_time=appointment_time,
                    arrival_time=arrival_time,
                    loading_start=loading_start,
                    loading_end=loading_end,
                    departure_time=departure_time,
                    detention_pay=(
                        _money((dwell_hours - 2) * 75, rng)
                        if dwell_hours > 2
                        else Decimal("0")
                    ),
                    driver_notes=notes,
                )
            )

    return tuple(dwell_events)


def _money(value: float, rng: random.Random) -> Decimal:
    adjusted = value + rng.uniform(-2.5, 2.5)
    return Decimal(str(round(max(0, adjusted), 2)))


def _p90(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = math.ceil(0.9 * len(ordered)) - 1
    return ordered[max(0, rank)]


def demo_facility_risk_summaries() -> dict[str, FacilityRiskSummary]:
    """Deterministic facility risk summaries derived from DEMO_FACILITY_VISIT_PLANS.

    Used by the load-evaluation mock-loads endpoint (TASK-036B), which has no
    database session, so it mirrors FacilityService._build_intelligence using
    only the seed's scripted visit plans.
    """
    summaries: dict[str, FacilityRiskSummary] = {}

    for facility in DEMO_FACILITIES:
        visits = DEMO_FACILITY_VISIT_PLANS.get(facility.name, ())
        dwell_values = [dwell_hours for dwell_hours, _ in visits]
        delay_minutes = [delay for _, delay in visits]

        avg_dwell = sum(dwell_values) / len(dwell_values) if dwell_values else None
        appt_visits = len(delay_minutes)
        appt_on_time = sum(
            1 for delay in delay_minutes if delay <= fi.APPOINTMENT_GRACE_MINUTES
        )
        reliability = fi.appointment_reliability(appt_visits, appt_on_time)

        detention_visits = sum(1 for hours in dwell_values if hours > fi.DETENTION_FREE_HOURS)
        excess_values = [max(0.0, hours - fi.DETENTION_FREE_HOURS) for hours in dwell_values]
        avg_excess = sum(excess_values) / len(excess_values) if excess_values else 0.0
        risk = fi.detention_risk(len(dwell_values), detention_visits, avg_excess)

        dwell = fi.dwell_score(avg_dwell) if avg_dwell is not None else None

        summaries[facility.name] = FacilityRiskSummary(
            facility_id=None,
            facility_name=facility.name,
            operational_score=fi.operational_score(dwell, reliability, risk),
            avg_dwell_hours=avg_dwell,
            p90_dwell_hours=_p90(dwell_values),
            appointment_reliability_pct=reliability,
            detention_risk_score=risk,
            detention_risk_band=fi.detention_risk_band(risk),
            visit_count=len(dwell_values),
            confidence=fi.confidence(len(dwell_values)),
        )

    return summaries
