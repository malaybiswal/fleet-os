from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    def __init__(self, dashboard_repository: DashboardRepository | None = None):
        self.dashboard_repository = dashboard_repository or DashboardRepository()

    def get_summary(
        self,
        db: Session,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        active_trucks = self.dashboard_repository.get_active_truck_count(db)
        avg_dwell_hours = self.dashboard_repository.get_avg_dwell_hours(
            db=db,
            start_date=start_date,
            end_date=end_date,
        )
        open_alerts = self.dashboard_repository.get_open_alert_count(db)
        open_loads = self.dashboard_repository.get_open_load_count(db)

        totals = self.dashboard_repository.get_delivered_load_totals(
            db=db,
            start_date=start_date,
            end_date=end_date,
        )

        total_revenue = totals["total_revenue"] or Decimal("0")
        total_miles = totals["total_miles"] or Decimal("0")
        total_deadhead_miles = totals["total_deadhead_miles"] or Decimal("0")
        total_fuel_cost = totals["total_fuel_cost"] or Decimal("0")

        if total_miles > 0:
            avg_revenue_per_mile = total_revenue / total_miles
            deadhead_percentage = float((total_deadhead_miles / total_miles) * 100)
            fuel_cost_per_mile = total_fuel_cost / total_miles
        else:
            avg_revenue_per_mile = Decimal("0")
            deadhead_percentage = 0.0
            fuel_cost_per_mile = Decimal("0")

        return {
            "active_trucks": active_trucks,
            "avg_dwell_hours": avg_dwell_hours,
            "total_revenue": total_revenue,
            "avg_revenue_per_mile": avg_revenue_per_mile,
            "deadhead_percentage": deadhead_percentage,
            "open_alerts": open_alerts,
            "open_loads": open_loads,
            "fuel_cost_per_mile": fuel_cost_per_mile,
        }