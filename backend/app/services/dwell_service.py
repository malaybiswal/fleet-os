from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.dwell_event import DwellEvent
from app.repositories.dwell_repository import DwellRepository
from app.services.alert_service import AlertService


class DwellService:
    def __init__(
        self,
        dwell_repository: DwellRepository | None = None,
        alert_service: AlertService | None = None,
    ):
        self.dwell_repository = dwell_repository or DwellRepository()
        self.alert_service = alert_service or AlertService()

    def calculate_dwell_hours(self, arrival: datetime, departure: datetime) -> float:
        return (departure - arrival).total_seconds() / 3600

    def calculate_loading_delay(self, appointment: datetime, loading_start: datetime) -> float:
        return (loading_start - appointment).total_seconds() / 3600

    def calculate_facility_score(self, avg_dwell_hours: float) -> float:
        return max(0, 100 - avg_dwell_hours * 10)

    def create_dwell_event(self, db: Session, dwell_event: DwellEvent, truck_id: str | None = None) -> DwellEvent:
        if dwell_event.arrival_time and dwell_event.departure_time:
            if dwell_event.arrival_time >= dwell_event.departure_time:
                raise HTTPException(
                    status_code=422,
                    detail="arrival_time must be before departure_time",
                )

        created = self.dwell_repository.create(db, dwell_event)

        if truck_id and created.arrival_time and created.departure_time:
            dwell_hours = self.calculate_dwell_hours(
                created.arrival_time,
                created.departure_time,
            )
            self.alert_service.check_dwell_alert(
                db=db,
                dwell_event=created,
                dwell_hours=dwell_hours,
                truck_id=truck_id,
            )

        return created

    def get_events(self, db: Session,  fleet_id: int, limit: int = 100, offset: int = 0):
        return self.dwell_repository.get_all(db, fleet_id=fleet_id, limit=limit, offset=offset)

    def get_facility_scorecard(
        self,
        db: Session,
        fleet_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        rows = self.dwell_repository.facility_scorecard(
            db=db,
            fleet_id=fleet_id,
            start_date=start_date,
            end_date=end_date,
        )

        result = []
        for row in rows:
            avg_dwell = float(row.avg_dwell_hours or 0)
            result.append(
                {
                    "facility_name": row.facility_name or "Unknown",
                    "avg_dwell_hours": avg_dwell,
                    "avg_loading_delay_hours": 0.0,
                    "total_detention_pay": row.total_detention_pay or 0,
                    "visit_count": row.visit_count,
                    "facility_score": self.calculate_facility_score(avg_dwell),
                }
            )

        return result

    def get_broker_scorecard(
        self,
        db: Session,
        fleet_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        rows = self.dwell_repository.broker_scorecard(
            db=db,
            fleet_id=fleet_id,
            start_date=start_date,
            end_date=end_date,
        )

        result = []
        for row in rows:
            result.append(
                {
                    "broker_name": row.broker_name or "Unknown",
                    "avg_dwell_hours": float(row.avg_dwell_hours or 0),
                    "avg_loading_delay_hours": 0.0,
                    "total_detention_pay": row.total_detention_pay or 0,
                    "load_count": row.load_count,
                }
            )

        return result