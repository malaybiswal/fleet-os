from sqlalchemy.orm import Session

from app.models.ingestion_run import IngestionRun
from app.repositories.base import BaseRepository
from app.schemas.ingestion_run import IngestionRunCreate, IngestionRunUpdate


class IngestionRunRepository(BaseRepository[IngestionRun]):
    def __init__(self):
        super().__init__(IngestionRun)

    def create_run(self, db: Session, run_create: IngestionRunCreate) -> IngestionRun:
        run = IngestionRun(**run_create.model_dump())
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def update_run(self, db: Session, run_id: int, update: IngestionRunUpdate) -> IngestionRun | None:
        run = self.get(db, run_id)
        if run is None:
            return None
        for field, value in update.model_dump(exclude_none=True).items():
            setattr(run, field, value)
        db.commit()
        db.refresh(run)
        return run

    def get_last_successful(
        self, db: Session, provider: str, entity_type: str
    ) -> IngestionRun | None:
        return (
            db.query(IngestionRun)
            .filter(
                IngestionRun.provider == provider,
                IngestionRun.entity_type == entity_type,
                IngestionRun.status == "completed",
            )
            .order_by(IngestionRun.completed_at.desc())
            .first()
        )
