from datetime import datetime
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.truck import Truck
from app.repositories.base import BaseRepository
from app.schemas.truck import TruckCreate


class TruckRepository(BaseRepository[Truck]):
    def __init__(self):
        super().__init__(Truck)

    def get_all(self, db: Session) -> list[Truck]:
        return db.query(Truck).order_by(Truck.truck_id.asc()).all()

    def get_by_truck_id(self, db: Session, truck_id: str) -> Truck | None:
        return db.query(Truck).filter(Truck.truck_id == truck_id).first()

    def get_active_count(self, db: Session) -> int:
        return db.query(Truck).filter(Truck.status == "active").count()

    def update_position(
        self,
        db: Session,
        truck_id: str,
        lat: Decimal | float | None,
        lon: Decimal | float | None,
        last_seen_at: datetime,
    ) -> Truck | None:
        truck = self.get_by_truck_id(db, truck_id)
        if truck is None:
            return None

        truck.current_lat = lat
        truck.current_lon = lon
        truck.last_seen_at = last_seen_at

        db.commit()
        db.refresh(truck)
        return truck

    def upsert_from_provider(
        self,
        db: Session,
        truck_create: TruckCreate,
        provider: str,
        provider_id: str,
        ingested_at: datetime,
    ) -> Truck:
        values = {
            **truck_create.model_dump(),
            "provider": provider,
            "provider_id": provider_id,
            "ingested_at": ingested_at,
        }
        stmt = pg_insert(Truck).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["provider", "provider_id"],
            index_where=text("provider IS NOT NULL"),
            set_={
                "status": stmt.excluded.status,
                "current_location": stmt.excluded.current_location,
                "current_lat": stmt.excluded.current_lat,
                "current_lon": stmt.excluded.current_lon,
                "last_seen_at": stmt.excluded.last_seen_at,
                "ingested_at": stmt.excluded.ingested_at,
            },
        )
        db.execute(stmt)
        db.commit()
        return self.get_by_truck_id(db, truck_create.truck_id)

    def get_trucks_by_provider_ids(
        self, db: Session, provider: str, provider_ids: list[str]
    ) -> dict[str, str]:
        rows = (
            db.query(Truck.provider_id, Truck.truck_id)
            .filter(Truck.provider == provider, Truck.provider_id.in_(provider_ids))
            .all()
        )
        return {row.provider_id: row.truck_id for row in rows}