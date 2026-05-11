import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.load import Load


def _money(min_value: float, max_value: float) -> Decimal:
    return Decimal(str(round(random.uniform(min_value, max_value), 2)))


def generate_loads(
    count: int,
    truck_ids: list[str],
    driver_ids: list[str],
    start_datetime: datetime,
    end_datetime: datetime,
) -> list[Load]:
    brokers = ["Coyote", "CH Robinson", "TQL", "Uber Freight", "Convoy"]
    cities = ["Austin, TX", "Dallas, TX", "Houston, TX", "San Antonio, TX", "Laredo, TX", "El Paso, TX"]
    statuses = ["in_transit", "delivered", "cancelled"]

    total_seconds = int((end_datetime - start_datetime).total_seconds())

    loads = []
    for i in range(1, count + 1):
        pickup_time = start_datetime + timedelta(seconds=random.randint(0, total_seconds))
        delivery_time = pickup_time + timedelta(hours=random.randint(4, 72))

        miles = _money(50, 2000)
        deadhead_miles = _money(0, min(500, float(miles)))

        loads.append(
            Load(
                load_id=f"LOAD-{i:04d}",
                truck_id=random.choice(truck_ids),
                driver_id=random.choice(driver_ids),
                broker_name=random.choice(brokers),
                origin=random.choice(cities),
                destination=random.choice(cities),
                revenue=_money(500, 5000),
                miles=miles,
                deadhead_miles=deadhead_miles,
                fuel_cost=_money(100, 1500),
                maintenance_reserve=_money(50, 500),
                driver_cost=_money(100, 2000),
                tolls=_money(0, 250),
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                status=random.choice(statuses),
            )
        )

    return loads