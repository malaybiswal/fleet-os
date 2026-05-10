from datetime import datetime

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.telemetry_event import TelemetryEvent
from app.repositories.base import BaseRepository


class TelemetryRepository(BaseRepository[TelemetryEvent]):
    def __init__(self):
        super().__init__(TelemetryEvent)

    def ingest(
        self,
        db: Session,
        telemetry: TelemetryEvent,
    ) -> TelemetryEvent:
        db.add(telemetry)
        db.commit()
        db.refresh(telemetry)
        return telemetry

    def latest_for_truck(
        self,
        db: Session,
        truck_id: str,
    ) -> TelemetryEvent | None:
        return (
            db.query(TelemetryEvent)
            .filter(TelemetryEvent.truck_id == truck_id)
            .order_by(desc(TelemetryEvent.timestamp))
            .first()
        )

    def latest_for_all_trucks(
        self,
        db: Session,
    ) -> list[TelemetryEvent]:
        subquery = (
            db.query(
                TelemetryEvent.truck_id,
                func.max(TelemetryEvent.timestamp).label("latest_ts"),
            )
            .group_by(TelemetryEvent.truck_id)
            .subquery()
        )

        return (
            db.query(TelemetryEvent)
            .join(
                subquery,
                (TelemetryEvent.truck_id == subquery.c.truck_id)
                & (TelemetryEvent.timestamp == subquery.c.latest_ts),
            )
            .all()
        )

    def get_idle_events(
        self,
        db: Session,
        minimum_idle_minutes: int = 60,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[TelemetryEvent]:
        query = db.query(TelemetryEvent).filter(
            TelemetryEvent.idle_minutes >= minimum_idle_minutes
        )

        if start_date is not None:
            query = query.filter(TelemetryEvent.timestamp >= start_date)

        if end_date is not None:
            query = query.filter(TelemetryEvent.timestamp <= end_date)

        return query.order_by(desc(TelemetryEvent.timestamp)).all()