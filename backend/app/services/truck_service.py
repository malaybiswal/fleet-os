from sqlalchemy.orm import Session

from app.repositories.truck_repository import TruckRepository


class TruckService:
    def __init__(self, truck_repository: TruckRepository | None = None):
        self.truck_repository = truck_repository or TruckRepository()

    def get_all_trucks(self, db: Session):
        return self.truck_repository.get_all(db)

    def truck_exists(self, db: Session, truck_id: str) -> bool:
        return self.truck_repository.get_by_truck_id(db, truck_id) is not None