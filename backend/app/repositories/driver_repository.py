from datetime import datetime

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.repositories.base import BaseRepository
from app.schemas.driver import DriverCreate


class DriverRepository(BaseRepository[Driver]):
    def __init__(self):
        super().__init__(Driver)

    def get_by_driver_id(self, db: Session, driver_id: str) -> Driver | None:
        return db.query(Driver).filter(Driver.driver_id == driver_id).first()

    def upsert_from_provider(
        self,
        db: Session,
        driver_create: DriverCreate,
        provider: str,
        provider_id: str,
        ingested_at: datetime,
    ) -> Driver:
        values = {
            **driver_create.model_dump(),
            "provider": provider,
            "provider_id": provider_id,
            "ingested_at": ingested_at,
        }
        stmt = pg_insert(Driver).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["provider", "provider_id"],
            index_where=text("provider IS NOT NULL"),
            set_={
                "name": stmt.excluded.name,
                "status": stmt.excluded.status,
                "ingested_at": stmt.excluded.ingested_at,
            },
        )
        db.execute(stmt)
        db.commit()
        return self.get_by_driver_id(db, driver_create.driver_id)
