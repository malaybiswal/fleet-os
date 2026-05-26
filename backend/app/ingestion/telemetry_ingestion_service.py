from sqlalchemy.orm import Session

from app.ingestion.normalized_events import NormalizedTelemetryEvent
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck


class UnknownTruckError(ValueError):
    pass


class TelemetryIngestionService:
    def __init__(self, db: Session, auto_create_trucks: bool = False):
        self.db = db
        self.auto_create_trucks = auto_create_trucks

    def ingest(self, event: NormalizedTelemetryEvent) -> TelemetryEvent:
        truck = (
            self.db.query(Truck)
            .filter(
                Truck.fleet_id == event.fleet_id,
                Truck.truck_id == event.truck_id,
            )
            .first()
        )

        if not truck:
            if not self.auto_create_trucks:
                raise UnknownTruckError(
                    f"Unknown truck_id={event.truck_id} for fleet_id={event.fleet_id}"
                )

            truck = Truck(
                truck_id=event.truck_id,
                fleet_id=event.fleet_id,
                status=event.status or "active",
                current_location=event.location_description,
                current_lat=event.latitude,
                current_lon=event.longitude,
                last_seen_at=event.timestamp,
            )

            self.db.add(truck)
            self.db.flush()
        else:
            truck.current_lat = event.latitude
            truck.current_lon = event.longitude
            truck.current_location = event.location_description
            truck.status = event.status or truck.status
            truck.last_seen_at = event.timestamp

        telemetry_event = TelemetryEvent(
            fleet_id=event.fleet_id,
            truck_id=event.truck_id,
            timestamp=event.timestamp,
            gps_lat=event.latitude,
            gps_lon=event.longitude,
            speed=event.speed_mph,
            heading=event.heading,
        )

        self.db.add(telemetry_event)
        self.db.commit()
        self.db.refresh(telemetry_event)

        return telemetry_event