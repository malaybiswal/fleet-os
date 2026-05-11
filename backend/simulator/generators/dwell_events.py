import random
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.dwell_event import DwellEvent


def generate_dwell_events(
    count: int,
    load_ids: list[str],
    start_datetime: datetime,
    end_datetime: datetime,
) -> list[DwellEvent]:
    facilities = ["Walmart DC", "HEB DC", "Kroger DC", "Costco DC", "Sysco Warehouse"]
    brokers = ["Coyote", "CH Robinson", "TQL", "Uber Freight", "Convoy"]

    total_seconds = int((end_datetime - start_datetime).total_seconds())

    events = []
    for i in range(count):
        appointment_time = start_datetime + timedelta(seconds=random.randint(0, total_seconds))
        arrival_time = appointment_time + timedelta(minutes=random.randint(-30, 120))
        loading_start = arrival_time + timedelta(minutes=random.randint(15, 180))
        loading_end = loading_start + timedelta(minutes=random.randint(30, 240))
        departure_time = loading_end + timedelta(minutes=random.randint(15, 120))

        events.append(
            DwellEvent(
                load_id=random.choice(load_ids),
                facility_name=random.choice(facilities),
                broker_name=random.choice(brokers),
                appointment_time=appointment_time,
                arrival_time=arrival_time,
                loading_start=loading_start,
                loading_end=loading_end,
                departure_time=departure_time,
                detention_pay=Decimal(str(round(random.uniform(0, 500), 2))),
                driver_notes="Synthetic dwell event",
            )
        )

    return events