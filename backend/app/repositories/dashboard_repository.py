from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.dwell_event import DwellEvent
from app.models.load import Load
from app.models.truck import Truck


class DashboardRepository:
    def get_active_truck_count(self, db: Session) -> int:
        return db.query(Truck).filter(Truck.status == "active").count()

    def get_open_alert_count(self, db: Session) -> int:
        return db.query(Alert).filter(Alert.resolved.is_(False)).count()

    def get_open_load_count(self, db: Session) -> int:
        return (
            db.query(Load)
            .filter(Load.status.notin_(["delivered", "cancelled"]))
            .count()
        )

    def get_avg_dwell_hours(
        self,
        db: Session,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> float:
        dwell_hours = (
            func.extract("epoch", DwellEvent.departure_time - DwellEvent.arrival_time)
            / 3600.0
        )

        query = db.query(func.coalesce(func.avg(dwell_hours), 0))

        if start_date is not None:
            query = query.filter(DwellEvent.arrival_time >= start_date)

        if end_date is not None:
            query = query.filter(DwellEvent.arrival_time <= end_date)

        return float(query.scalar() or 0)

    def get_delivered_load_totals(
        self,
        db: Session,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Decimal | int]:
        query = db.query(
            func.coalesce(func.sum(Load.revenue), 0).label("total_revenue"),
            func.coalesce(func.sum(Load.miles), 0).label("total_miles"),
            func.coalesce(func.sum(Load.deadhead_miles), 0).label("total_deadhead_miles"),
            func.coalesce(func.sum(Load.fuel_cost), 0).label("total_fuel_cost"),
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
            "total_deadhead_miles": row.total_deadhead_miles,
            "total_fuel_cost": row.total_fuel_cost,
            "delivered_count": row.delivered_count,
        }