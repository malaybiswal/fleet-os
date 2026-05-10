from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.dwell_event import DwellEvent
from app.repositories.base import BaseRepository


class DwellRepository(BaseRepository[DwellEvent]):
    def __init__(self):
        super().__init__(DwellEvent)

    def create(
        self,
        db: Session,
        dwell_event: DwellEvent,
    ) -> DwellEvent:
        db.add(dwell_event)
        db.commit()
        db.refresh(dwell_event)
        return dwell_event

    def get_by_load_id(
        self,
        db: Session,
        load_id: str,
    ) -> list[DwellEvent]:
        return (
            db.query(DwellEvent)
            .filter(DwellEvent.load_id == load_id)
            .order_by(DwellEvent.arrival_time.desc())
            .all()
        )

    def facility_scorecard(
        self,
        db: Session,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        dwell_hours = (
            func.extract(
                "epoch",
                DwellEvent.departure_time - DwellEvent.arrival_time,
            )
            / 3600.0
        )

        query = db.query(
            DwellEvent.facility_name.label("facility_name"),
            func.avg(dwell_hours).label("avg_dwell_hours"),
            func.sum(DwellEvent.detention_pay).label("total_detention_pay"),
            func.count(DwellEvent.id).label("visit_count"),
        )

        if start_date is not None:
            query = query.filter(DwellEvent.arrival_time >= start_date)

        if end_date is not None:
            query = query.filter(DwellEvent.arrival_time <= end_date)

        return (
            query.group_by(DwellEvent.facility_name)
            .order_by(func.avg(dwell_hours).desc())
            .all()
        )

    def broker_scorecard(
        self,
        db: Session,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        dwell_hours = (
            func.extract(
                "epoch",
                DwellEvent.departure_time - DwellEvent.arrival_time,
            )
            / 3600.0
        )

        query = db.query(
            DwellEvent.broker_name.label("broker_name"),
            func.avg(dwell_hours).label("avg_dwell_hours"),
            func.sum(DwellEvent.detention_pay).label("total_detention_pay"),
            func.count(DwellEvent.id).label("load_count"),
        )

        if start_date is not None:
            query = query.filter(DwellEvent.arrival_time >= start_date)

        if end_date is not None:
            query = query.filter(DwellEvent.arrival_time <= end_date)

        return (
            query.group_by(DwellEvent.broker_name)
            .order_by(func.avg(dwell_hours).desc())
            .all()
        )
    
    def get_all(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DwellEvent]:
        return (
            db.query(DwellEvent)
            .order_by(DwellEvent.arrival_time.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )