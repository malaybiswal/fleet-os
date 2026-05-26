from sqlalchemy.orm import Session

from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.schemas.live_position import LiveTruckPosition


def get_live_positions_for_fleet(
    db: Session,
    fleet_id: int,
) -> list[LiveTruckPosition]:
    trucks = (
        db.query(Truck)
        .filter(Truck.fleet_id == fleet_id)
        .order_by(Truck.truck_id)
        .all()
    )

    positions: list[LiveTruckPosition] = []

    for truck in trucks:
        latest_event = (
            db.query(TelemetryEvent)
            .filter(
                TelemetryEvent.fleet_id == fleet_id,
                TelemetryEvent.truck_id == truck.truck_id,
            )
            .order_by(TelemetryEvent.timestamp.desc())
            .first()
        )

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