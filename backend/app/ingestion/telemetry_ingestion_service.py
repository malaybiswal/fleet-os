from sqlalchemy.orm import Session

from app.ingestion.normalized_events import NormalizedTelemetryEvent
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.services.alert_service import AlertService
from app.services.operational_status import derive_operational_status


class UnknownTruckError(ValueError):
    pass


class TelemetryIngestionService:
    def __init__(
        self,
        db: Session,
        auto_create_trucks: bool = False,
        alert_service: AlertService | None = None,
    ):
        self.db = db
        self.auto_create_trucks = auto_create_trucks
        self.alert_service = alert_service or AlertService()

    def ingest(self, event: NormalizedTelemetryEvent) -> TelemetryEvent:
        truck = (
            self.db.query(Truck)
            .filter(
                Truck.fleet_id == event.fleet_id,
                Truck.truck_id == event.truck_id,
            )
            .first()
        )
        operational_status = derive_operational_status(
            speed_mph=event.speed_mph,
            reported_status=event.status,
            current_status=truck.status if truck else None,
        )

        if not truck:
            if not self.auto_create_trucks:
                raise UnknownTruckError(
                    f"Unknown truck_id={event.truck_id} for fleet_id={event.fleet_id}"
                )

            truck = Truck(
                truck_id=event.truck_id,
                fleet_id=event.fleet_id,
                status=operational_status,
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
            truck.status = operational_status
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

        self.alert_service.evaluate_telemetry_alerts(
            db=self.db,
            fleet_id=event.fleet_id,
            telemetry_event=telemetry_event,
            operational_status=operational_status,
        )

        return telemetry_event
