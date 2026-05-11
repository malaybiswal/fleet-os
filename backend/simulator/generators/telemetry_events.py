import random
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.telemetry_event import TelemetryEvent


def _decimal(value: float, places: int = 2) -> Decimal:
    return Decimal(str(round(value, places)))


def generate_telemetry_events(
    count: int,
    truck_ids: list[str],
    start_datetime: datetime,
    end_datetime: datetime,
    alert_frequency: float = 0.1,
) -> list[TelemetryEvent]:
    total_seconds = int((end_datetime - start_datetime).total_seconds())

    events = []
    for _ in range(count):
        truck_id = random.choice(truck_ids)
        timestamp = start_datetime + timedelta(seconds=random.randint(0, total_seconds))

        trigger_alert = random.random() < alert_frequency

        fuel_level = random.uniform(0, 14) if trigger_alert else random.uniform(15, 100)
        engine_temp = random.uniform(231, 250) if trigger_alert and random.choice([True, False]) else random.uniform(150, 230)
        reefer_temp = random.choice([random.uniform(25, 33), random.uniform(39, 50)]) if trigger_alert and random.choice([True, False]) else random.uniform(34, 38)

        events.append(
            TelemetryEvent(
                truck_id=truck_id,
                timestamp=timestamp,
                speed=_decimal(random.uniform(0, 80)),
                rpm=random.randint(500, 2200),
                engine_temp=_decimal(engine_temp),
                fuel_level=_decimal(fuel_level),
                gps_lat=_decimal(random.uniform(25.0, 36.5), 6),
                gps_lon=_decimal(random.uniform(-106.0, -93.0), 6),
                idle_minutes=random.randint(0, 180),
                reefer_temp=_decimal(reefer_temp),
                load_weight=_decimal(random.uniform(5000, 45000)),
            )
        )

    return events