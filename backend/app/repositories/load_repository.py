from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.load import Load
from app.repositories.base import BaseRepository


class LoadRepository(BaseRepository[Load]):
    def __init__(self):
        super().__init__(Load)

    def create(self, db: Session, load: Load) -> Load:
        db.add(load)
        db.commit()
        db.refresh(load)
        return load

    def get_all(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Load]:
        query = db.query(Load)

        if start_date is not None:
            query = query.filter(Load.pickup_time >= start_date)
        if end_date is not None:
            query = query.filter(Load.pickup_time <= end_date)

        return (
            query.order_by(Load.pickup_time.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_all_by_fleet(self, db: Session, fleet_id: int) -> list[Load]:
        return (
            db.query(Load)
            .filter(Load.fleet_id == fleet_id)
            .order_by(Load.load_id.asc())
            .all()
        )
        
    def get_by_id(self, db: Session, load_id: str) -> Load | None:
        return db.query(Load).filter(Load.load_id == load_id).first()

    def get_delivered_totals(
        self,
        db: Session,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Decimal]:
        query = db.query(
            func.coalesce(func.sum(Load.revenue), 0).label("total_revenue"),
            func.coalesce(func.sum(Load.miles), 0).label("total_miles"),
            func.coalesce(func.sum(Load.fuel_cost), 0).label("total_fuel_cost"),
            func.coalesce(func.sum(Load.deadhead_miles), 0).label("total_deadhead_miles"),
            func.count(Load.id).label("delivered_count"),
        ).filter(Load.status == "delivered")

        if start_date is not None:
            query = query.filter(Load.pickup_time >= start_date)
        if end_date is not None:
            query = query.filter(Load.pickup_time <= end_date)

        row = query.one()

        return {
            "total_revenue": row.total_revenue,
            "total_miles": row.total_miles,
            "total_fuel_cost": row.total_fuel_cost,
            "total_deadhead_miles": row.total_deadhead_miles,
            "delivered_count": row.delivered_count,
        }

    def get_open_count(self, db: Session) -> int:
        return (
            db.query(Load)
            .filter(Load.status.notin_(["delivered", "cancelled"]))
            .count()
        )