from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.telemetry_event import TelemetryEvent
from app.repositories.telemetry_repository import TelemetryRepository
from app.repositories.truck_repository import TruckRepository
from app.services.alert_service import AlertService


class TelemetryService:
    def __init__(
        self,
        telemetry_repository: TelemetryRepository | None = None,
        truck_repository: TruckRepository | None = None,
        alert_service: AlertService | None = None,
    ):
        self.telemetry_repository = telemetry_repository or TelemetryRepository()
        self.truck_repository = truck_repository or TruckRepository()
        self.alert_service = alert_service or AlertService()

    def ingest_telemetry(
        self,
        db: Session,
        telemetry_event: TelemetryEvent,
        fleet_id: int,
    ) -> TelemetryEvent:
        truck = self.truck_repository.get_by_truck_id(
            db=db,
            truck_id=telemetry_event.truck_id,
        )

        if truck is None:
            raise HTTPException(
                status_code=404,
                detail=f"Truck {telemetry_event.truck_id} not found",
            )

        if truck.fleet_id != fleet_id:
            raise HTTPException(
                status_code=404,
                detail=f"Truck {telemetry_event.truck_id} not found",
            )

        created = self.telemetry_repository.ingest(db, telemetry_event)

        self.truck_repository.update_position(
            db=db,
            truck_id=created.truck_id,
            lat=created.gps_lat,
            lon=created.gps_lon,
            last_seen_at=created.timestamp,
        )

        self.alert_service.check_telemetry_alerts(
            db=db,
            telemetry_event=created,
            fleet_id=fleet_id,
        )

        return created

    def get_telemetry_for_truck(
        self,
        db: Session,
        truck_id: str,
        fleet_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TelemetryEvent]:
        truck = self.truck_repository.get_by_truck_id(db=db, truck_id=truck_id)

        if truck is None:
            raise HTTPException(
                status_code=404,
                detail=f"Truck {truck_id} not found",
            )

        if truck.fleet_id != fleet_id:
            raise HTTPException(
                status_code=404,
                detail=f"Truck {truck_id} not found",
            )

        return self.telemetry_repository.get_by_truck_id(
            db=db,
            truck_id=truck_id,
            limit=limit,
            offset=offset,
        )