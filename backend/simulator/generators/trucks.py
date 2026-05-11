import random

from app.models.truck import Truck


def generate_trucks(count: int) -> list[Truck]:
    statuses = ["active", "idle", "maintenance"]
    cities = ["Austin, TX", "Dallas, TX", "Houston, TX", "San Antonio, TX", "Laredo, TX"]

    trucks = []
    for i in range(1, count + 1):
        trucks.append(
            Truck(
                truck_id=f"TRUCK-{i:03d}",
                status=random.choice(statuses),
                current_location=random.choice(cities),
            )
        )

    return trucks