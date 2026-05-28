from app.seed.types import DriverSeed, TruckSeed
from app.simulator.telemetry import TelemetryEventSeed
from app.services.operational_status import derive_operational_status

DEMO_DRIVERS: tuple[DriverSeed, ...] = tuple(
    DriverSeed(
        driver_id=f"DEMO-DRIVER-{index:03d}",
        fleet_key="operations" if index <= 5 else "refrigerated",
        name=f"Demo Driver {index:03d}",
        status="on_load" if index in {1, 2, 3, 6} else "available",
    )
    for index in range(1, 7)
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
