import random

from app.models.alert import Alert


def generate_alerts(
    count: int,
    truck_ids: list[str],
) -> list[Alert]:
    alert_types = ["high_dwell", "low_fuel", "reefer_temp_deviation", "engine_overheat", "speeding"]
    severities = ["low", "medium", "high"]

    alerts = []
    for i in range(1, count + 1):
        truck_id = random.choice(truck_ids)
        alert_type = random.choice(alert_types)
        alerts.append(
            Alert(
                truck_id=truck_id,
                severity=random.choice(severities),
                alert_type=alert_type,
                message=f"Synthetic alert {i}: {alert_type} for truck {truck_id}",
                resolved=random.choice([False, False, False, True]),
            )
        )

    return alerts