from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.dwell_event import DwellEvent
from app.models.facility import Facility, normalize_facility_name
from app.models.load import Load
from app.repositories.base import BaseRepository


class FacilityRepository(BaseRepository[Facility]):
    def __init__(self):
        super().__init__(Facility)

    def get_or_create(self, db: Session, fleet_id: int, name: str) -> Facility:
        normalized = normalize_facility_name(name)
        facility = (
            db.query(Facility)
            .filter(
                Facility.fleet_id == fleet_id,
                Facility.normalized_name == normalized,
            )
            .first()
        )
        if facility:
            return facility

        facility = Facility(fleet_id=fleet_id, name=name.strip(), normalized_name=normalized)
        db.add(facility)
        try:
            db.commit()
        except IntegrityError:
            # Lost a concurrent-insert race on (fleet_id, normalized_name).
            db.rollback()
            facility = (
                db.query(Facility)
                .filter(
                    Facility.fleet_id == fleet_id,
                    Facility.normalized_name == normalized,
                )
                .first()
            )
            if facility is None:
                raise
            return facility
        db.refresh(facility)
        return facility

    def list_for_fleet(self, db: Session, fleet_id: int) -> list[Facility]:
        return (
            db.query(Facility)
            .filter(Facility.fleet_id == fleet_id)
            .order_by(Facility.name)
            .all()
        )

    def get_by_id(self, db: Session, fleet_id: int, facility_id: int) -> Facility | None:
        return (
            db.query(Facility)
            .filter(Facility.id == facility_id, Facility.fleet_id == fleet_id)
            .first()
        )

    def dwell_rows_for_intelligence(
        self,
        db: Session,
        fleet_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        facility_id: int | None = None,
    ) -> list[tuple[Facility | None, DwellEvent]]:
        """Dwell events with their facility, fleet-scoped through the loads join
        (matching facility_scorecard). Metrics are aggregated in Python so the
        same code runs on PostgreSQL and the SQLite test databases.
        """
        query = (
            db.query(Facility, DwellEvent)
            .select_from(DwellEvent)
            .outerjoin(Facility, Facility.id == DwellEvent.facility_id)
            .join(Load, Load.load_id == DwellEvent.load_id)
            .filter(Load.fleet_id == fleet_id)
            .filter(
                (DwellEvent.facility_id.isnot(None))
                | (DwellEvent.facility_name.isnot(None))
            )
        )

        if facility_id is not None:
            query = query.filter(DwellEvent.facility_id == facility_id)
        if start_date is not None:
            query = query.filter(DwellEvent.arrival_time >= start_date)
        if end_date is not None:
            query = query.filter(DwellEvent.arrival_time <= end_date)

        return query.order_by(DwellEvent.arrival_time.desc()).all()
