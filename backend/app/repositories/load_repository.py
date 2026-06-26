from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.load import Load
from app.repositories.base import BaseRepository


CANDIDATE_STATUSES: frozenset[str] = frozenset({"available"})
ACTIVE_ASSIGNMENT_STATUSES: frozenset[str] = frozenset({"booked", "in_transit"})


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

    def get_candidate_loads_by_fleet(self, db: Session, fleet_id: int) -> list[Load]:
        return (
            db.query(Load)
            .filter(Load.fleet_id == fleet_id, Load.status.in_(CANDIDATE_STATUSES))
            .order_by(Load.load_id.asc())
            .all()
        )

    def get_active_assignments_by_fleet(
        self,
        db: Session,
        fleet_id: int,
    ) -> tuple[set[str], set[str]]:
        rows = (
            db.query(Load.truck_id, Load.driver_id)
            .filter(
                Load.fleet_id == fleet_id,
                Load.status.in_(ACTIVE_ASSIGNMENT_STATUSES),
            )
            .all()
        )

        truck_ids = {truck_id for truck_id, _ in rows if truck_id is not None}
        driver_ids = {driver_id for _, driver_id in rows if driver_id is not None}
        return truck_ids, driver_ids

    def get_by_id(self, db: Session, load_id: str) -> Load | None:
        return db.query(Load).filter(Load.load_id == load_id).first()

    def get_by_id_and_fleet(
        self,
        db: Session,
        load_id: str,
        fleet_id: int,
    ) -> Load | None:
        return (
            db.query(Load)
            .filter(Load.load_id == load_id, Load.fleet_id == fleet_id)
            .first()
        )

    def assign(
        self,
        db: Session,
        load: Load,
        truck_id: str,
        driver_id: str,
    ) -> Load:
        load.truck_id = truck_id
        load.driver_id = driver_id
        load.status = "booked"
        db.commit()
        db.refresh(load)
        return load

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

    def delete_by_fleet_and_source(
        self,
        db: Session,
        fleet_id: int,
        source: str,
    ) -> int:
        deleted = (
            db.query(Load)
            .filter(Load.fleet_id == fleet_id, Load.source == source)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted

    def get_open_count(self, db: Session) -> int:
        return (
            db.query(Load)
            .filter(Load.status.notin_(["delivered", "cancelled"]))
            .count()
        )
