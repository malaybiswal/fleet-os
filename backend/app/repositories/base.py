from typing import Generic, Type, TypeVar

from sqlalchemy.orm import Session

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, entity_id: int) -> ModelType | None:
        return db.query(self.model).filter(self.model.id == entity_id).first()

    def list_all(self, db: Session) -> list[ModelType]:
        return db.query(self.model).all()

    def create(self, db: Session, obj: ModelType) -> ModelType:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, entity_id: int) -> bool:
        entity = self.get(db, entity_id)
        if not entity:
            return False

        db.delete(entity)
        db.commit()
        return True