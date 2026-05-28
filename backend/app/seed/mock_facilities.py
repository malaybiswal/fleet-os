from datetime import datetime, timedelta
from decimal import Decimal
import random

from app.seed.types import DwellEventSeed

DEMO_DWELL_SCENARIOS = (
    ("DEMO-LOAD-GOOD", "operations", "Houston Crossdock", "CH Robinson", 1.2, "Fast unload, reliable appointment."),
    ("DEMO-LOAD-HIGH-PAY-BAD", "operations", "Denver West DC", "Coyote", 3.8, "Long check-in and unload window."),
    ("DEMO-LOAD-HIGH-DWELL", "refrigerated", "Dallas Mega Cold Storage", "Cold Chain Logistics", 7.1, "High dwell risk facility for reefer freight."),
    ("DEMO-LOAD-STRONG-RELOAD", "operations", "Atlanta Reload Hub", "Uber Freight", 1.4, "Strong reload market and fast turn."),
    ("DEMO-LOAD-BAD-DEADHEAD", "operations", "Oklahoma Pipe Yard", "TQL", 2.6, "Deadhead-heavy lane with average dock time."),
    ("DEMO-LOAD-WEAK-BROKER", "operations", "Phoenix Grocery DC", "TQL Risk Desk", 5.4, "Weak broker communication and detention dispute risk."),
)


def build_demo_dwell_events(
    base_date: datetime,
    rng: random.Random,
) -> tuple[DwellEventSeed, ...]:
    dwell_events: list[DwellEventSeed] = []
    for index, (load_id, fleet_key, facility, broker, dwell_hours, notes) in enumerate(DEMO_DWELL_SCENARIOS):
        appointment_time = base_date + timedelta(hours=index * 2)
        arrival_time = appointment_time + timedelta(minutes=15 + index * 3)
        loading_start = arrival_time + timedelta(minutes=25 + index * 4)
        loading_end = loading_start + timedelta(hours=max(0.5, dwell_hours - 1.0))
        departure_time = arrival_time + timedelta(hours=dwell_hours)

        dwell_events.append(
            DwellEventSeed(
                load_id=load_id,
                fleet_key=fleet_key,
                facility_name=facility,
                broker_name=broker,
                appointment_time=appointment_time,
                arrival_time=arrival_time,
                loading_start=loading_start,
                loading_end=loading_end,
                departure_time=departure_time,
                detention_pay=_money(max(0, (dwell_hours - 2) * 75), rng),
                driver_notes=notes,
            )
        )

    return tuple(dwell_events)


def _money(value: float, rng: random.Random) -> Decimal:
    adjusted = value + rng.uniform(-2.5, 2.5)
    return Decimal(str(round(max(0, adjusted), 2)))
