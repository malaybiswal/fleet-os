from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.truck import Truck
from app.repositories.base import BaseRepository
from app.services.operational_status import OPERATIONALLY_ACTIVE_STATUSES


class TruckRepository(BaseRepository[Truck]):
    def __init__(self):
        super().__init__(Truck)

    def get_all(self, db: Session) -> list[Truck]:
        return db.query(Truck).order_by(Truck.truck_id.asc()).all()

    def get_all_by_fleet(self, db: Session, fleet_id: int) -> list[Truck]:
        return (
            db.query(Truck)
            .filter(Truck.fleet_id == fleet_id)
            .order_by(Truck.truck_id.asc())
            .all()
        )
        
    def get_by_truck_id(self, db: Session, truck_id: str) -> Truck | None:
        return db.query(Truck).filter(Truck.truck_id == truck_id).first()

    def get_active_count(self, db: Session) -> int:
        return (
            db.query(Truck)
            .filter(Truck.status.in_(OPERATIONALLY_ACTIVE_STATUSES))
            .count()
        )

    def update_position(
        self,
        db: Session,
        truck_id: str,
        lat: Decimal | float | None,
        lon: Decimal | float | None,
        last_seen_at: datetime,
        status: str | None = None,
    ) -> Truck | None:
        truck = self.get_by_truck_id(db, truck_id)
        if truck is None:
            return None

        truck.current_lat = lat
        truck.current_lon = lon
        truck.last_seen_at = last_seen_at
        if status is not None:
            truck.status = status

        db.commit()
        db.refresh(truck)
        return truck
