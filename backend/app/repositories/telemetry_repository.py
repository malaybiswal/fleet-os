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

    def get_by_truck_id(
        self,
        db: Session,
        truck_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TelemetryEvent]:
        return (
            db.query(TelemetryEvent)
            .filter(TelemetryEvent.truck_id == truck_id)
            .order_by(TelemetryEvent.timestamp.desc())
            .limit(limit)
            .offset(offset)
            .all()
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

    def get_latest_positions(
        self,
        db: Session,
        fleet_id: int,
    ) -> list[TelemetryEvent]:
        ranked_events = (
            db.query(
                TelemetryEvent.id.label("id"),
                func.row_number()
                .over(
                    partition_by=TelemetryEvent.truck_id,
                    order_by=[
                        TelemetryEvent.timestamp.desc(),
                        TelemetryEvent.id.desc(),
                    ],
                )
                .label("row_number"),
            )
            .filter(TelemetryEvent.fleet_id == fleet_id)
            .subquery()
        )

        return (
            db.query(TelemetryEvent)
            .join(ranked_events, TelemetryEvent.id == ranked_events.c.id)
            .filter(ranked_events.c.row_number == 1)
            .order_by(TelemetryEvent.truck_id.asc())
            .all()
        )

    def get_truck_history(
        self,
        db: Session,
        fleet_id: int,
        truck_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TelemetryEvent]:
        query = db.query(TelemetryEvent).filter(
            TelemetryEvent.fleet_id == fleet_id,
            TelemetryEvent.truck_id == truck_id,
        )

        if start_time is not None:
            query = query.filter(TelemetryEvent.timestamp >= start_time)

        if end_time is not None:
            query = query.filter(TelemetryEvent.timestamp <= end_time)

        return (
            query.order_by(
                TelemetryEvent.timestamp.desc(),
                TelemetryEvent.id.desc(),
            )
            .limit(limit)
            .offset(offset)
            .all()
        )

