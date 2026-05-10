from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.truck import Truck
from app.repositories.base import BaseRepository


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