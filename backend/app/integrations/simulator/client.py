from datetime import datetime, timezone
from random import choice, uniform


def fetch_simulated_vehicle_payloads() -> list[dict]:
    locations = [
        ("Austin, TX", 30.2672, -97.7431),
        ("Dallas, TX", 32.7767, -96.7970),
        ("Houston, TX", 29.7604, -95.3698),
        ("Laredo, TX", 27.5306, -99.4803),
    ]

    payloads = []

    for truck_number in range(1, 6):
        location_name, lat, lon = choice(locations)

        status = choice(["active", "idle", "maintenance"])

        if status == "active":
            speed_mph = round(uniform(45, 75), 2)

        elif status == "idle":
            speed_mph = round(uniform(0, 5), 2)

        else:
            speed_mph = 0

        payloads.append(
            {
                "vehicle_id": f"SIM-{truck_number:03}",
                "fleet_id": 17,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location": {
                    "description": location_name,
                    "lat": lat + uniform(-0.01, 0.01),
                    "lon": lon + uniform(-0.01, 0.01),
                },
                "speed_mph": speed_mph,
                "status": status,
            }
        )

    return payloads
