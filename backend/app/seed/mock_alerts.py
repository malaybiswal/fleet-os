from datetime import datetime, timedelta

from app.seed.types import AlertSeed


def build_demo_alerts(base_date: datetime) -> tuple[AlertSeed, ...]:
    return (
        AlertSeed(
            truck_id="DEMO-TRUCK-003",
            fleet_key="refrigerated",
            severity="high",
            alert_type="high_dwell",
            message="High dwell risk at Dallas Mega Cold Storage for DEMO-LOAD-HIGH-DWELL",
            created_at=base_date + timedelta(hours=4),
            resolved=False,
        ),
        AlertSeed(
            truck_id="DEMO-TRUCK-006",
            fleet_key="operations",
            severity="medium",
            alert_type="broker_risk",
            message="Weak broker history: detention disputes and slow communication on DEMO-LOAD-WEAK-BROKER",
            created_at=base_date + timedelta(hours=5),
            resolved=False,
        ),
        AlertSeed(
            truck_id="DEMO-TRUCK-001",
            fleet_key="operations",
            severity="medium",
            alert_type="low_fuel",
            message="Fuel level trending down on live Dallas to Houston route",
            created_at=base_date + timedelta(hours=6),
            resolved=False,
        ),
        AlertSeed(
            truck_id="DEMO-TRUCK-005",
            fleet_key="operations",
            severity="high",
            alert_type="engine_overheat",
            message="Maintenance truck held out of service for engine inspection",
            created_at=base_date + timedelta(hours=7),
            resolved=False,
        ),
        AlertSeed(
            truck_id="DEMO-TRUCK-003",
            fleet_key="refrigerated",
            severity="high",
            alert_type="reefer_temp_deviation",
            message="Reefer temperature requires review before next pickup",
            created_at=base_date + timedelta(hours=8),
            resolved=True,
        ),
    )
