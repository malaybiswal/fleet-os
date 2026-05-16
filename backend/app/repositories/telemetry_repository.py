from datetime import datetime

from sqlalchemy import desc, func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.telemetry_event import TelemetryEvent
from app.repositories.base import BaseRepository
from app.schemas.telemetry_event import TelemetryEventCreate


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

    def upsert_from_provider(
        self,
        db: Session,
        event_create: TelemetryEventCreate,
        provider: str,
        provider_id: str,
        ingested_at: datetime,
    ) -> None:
        values = {
            **event_create.model_dump(),
            "provider": provider,
            "provider_id": provider_id,
            "ingested_at": ingested_at,
        }
        stmt = pg_insert(TelemetryEvent).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["provider", "provider_id"],
            index_where=text("provider IS NOT NULL"),
            set_={
                "speed": stmt.excluded.speed,
                "rpm": stmt.excluded.rpm,
                "engine_temp": stmt.excluded.engine_temp,
                "fuel_level": stmt.excluded.fuel_level,
                "gps_lat": stmt.excluded.gps_lat,
                "gps_lon": stmt.excluded.gps_lon,
                "idle_minutes": stmt.excluded.idle_minutes,
                "reefer_temp": stmt.excluded.reefer_temp,
                "load_weight": stmt.excluded.load_weight,
                "ingested_at": stmt.excluded.ingested_at,
            },
        )
        db.execute(stmt)
        db.commit()