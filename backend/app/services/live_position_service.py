from sqlalchemy.orm import Session

from app.repositories.telemetry_repository import TelemetryRepository
from app.repositories.truck_repository import TruckRepository
from app.schemas.live_position import LiveTruckPosition


def get_live_positions_for_fleet(
    db: Session,
    fleet_id: int,
) -> list[LiveTruckPosition]:
    truck_repository = TruckRepository()
    telemetry_repository = TelemetryRepository()

    trucks = truck_repository.get_all_by_fleet(db, fleet_id)
    latest_events = telemetry_repository.get_latest_positions(db, fleet_id)
    latest_event_by_truck_id = {
        latest_event.truck_id: latest_event for latest_event in latest_events
    }

    positions: list[LiveTruckPosition] = []

    for truck in trucks:
        latest_event = latest_event_by_truck_id.get(truck.truck_id)

        positions.append(
            LiveTruckPosition(
                truck_id=truck.truck_id,
                status=truck.status,
                latitude=float(truck.current_lat)
                if truck.current_lat is not None
                else None,
                longitude=float(truck.current_lon)
                if truck.current_lon is not None
                else None,
                speed=float(latest_event.speed)
                if latest_event and latest_event.speed is not None
                else None,
                heading=latest_event.heading
                if latest_event and latest_event.heading is not None
                else None,
                last_seen_at=truck.last_seen_at,
                current_location=truck.current_location,
            )
        )

    return positions
