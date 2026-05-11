import random

from app.models.driver import Driver


def generate_drivers(count: int) -> list[Driver]:
    statuses = ["available", "on_load", "off_duty"]

    drivers = []
    for i in range(1, count + 1):
        drivers.append(
            Driver(
                driver_id=f"DRIVER-{i:03d}",
                name=f"Driver {i:03d}",
                status=random.choice(statuses),
            )
        )

    return drivers