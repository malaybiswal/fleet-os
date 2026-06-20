from decimal import Decimal

from app.seed.types import DriverSeed, TruckSeed
from app.simulator.telemetry import TelemetryEventSeed
from app.services.operational_status import derive_operational_status

# HOS values exercise three demo-relevant states for Phase 2 pairing:
# active-load drivers have reduced HOS; DEMO-DRIVER-005 is near-exhausted (1.5h)
# for the HOS-infeasibility path. DEMO-DRIVER-007 is genuinely unassigned and
# pairs with DEMO-TRUCK-007 as the free truck for candidate-load decisions.
DEMO_DRIVERS: tuple[DriverSeed, ...] = (
    DriverSeed(driver_id="DEMO-DRIVER-001", fleet_key="operations",    name="Demo Driver 001", status="available", hos_hours_remaining=Decimal("6.5")),
    DriverSeed(driver_id="DEMO-DRIVER-002", fleet_key="operations",    name="Demo Driver 002", status="on_load",   hos_hours_remaining=Decimal("8.0")),
    DriverSeed(driver_id="DEMO-DRIVER-003", fleet_key="operations",    name="Demo Driver 003", status="available", hos_hours_remaining=Decimal("4.5")),
    DriverSeed(driver_id="DEMO-DRIVER-004", fleet_key="operations",    name="Demo Driver 004", status="available", hos_hours_remaining=Decimal("10.0")),
    DriverSeed(driver_id="DEMO-DRIVER-005", fleet_key="operations",    name="Demo Driver 005", status="available", hos_hours_remaining=Decimal("1.5")),
    DriverSeed(driver_id="DEMO-DRIVER-006", fleet_key="refrigerated",  name="Demo Driver 006", status="on_load",   hos_hours_remaining=Decimal("7.0")),
    DriverSeed(driver_id="DEMO-DRIVER-007", fleet_key="operations",    name="Demo Driver 007", status="available", hos_hours_remaining=Decimal("11.0")),
)


def build_demo_trucks_from_latest_telemetry(
    telemetry_events: tuple[TelemetryEventSeed, ...],
) -> tuple[TruckSeed, ...]:
    latest_by_truck: dict[str, TelemetryEventSeed] = {}
    for event in telemetry_events:
        current = latest_by_truck.get(event.truck_id)
        if current is None or event.timestamp > current.timestamp:
            latest_by_truck[event.truck_id] = event

    trucks = []
    for truck_id in sorted(latest_by_truck):
        latest = latest_by_truck[truck_id]
        trucks.append(
            TruckSeed(
                truck_id=truck_id,
                fleet_key=latest.fleet_key,
                status=derive_operational_status(
                    speed_mph=latest.speed,
                    reported_status=latest.reported_status,
                ),
                current_location=latest.location_description,
                current_lat=latest.latitude,
                current_lon=latest.longitude,
                last_seen_at=latest.timestamp,
            )
        )

    return tuple(trucks)
