from decimal import Decimal

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.repositories.base import BaseRepository


class DriverRepository(BaseRepository[Driver]):
    def __init__(self):
        super().__init__(Driver)

    def get_available_by_fleet(
        self,
        db: Session,
        fleet_id: int,
        min_hos_hours: Decimal,
    ) -> list[Driver]:
        return (
            db.query(Driver)
            .filter(
                Driver.fleet_id == fleet_id,
                Driver.status == "available",
                or_(
                    Driver.hos_hours_remaining.is_(None),
                    Driver.hos_hours_remaining >= min_hos_hours,
                ),
            )
            .order_by(Driver.driver_id.asc())
            .all()
        )
