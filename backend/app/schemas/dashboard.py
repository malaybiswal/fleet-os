from decimal import Decimal

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    active_trucks: int
    avg_dwell_hours: float
    total_revenue: Decimal
    avg_revenue_per_mile: Decimal
    deadhead_percentage: float
    open_alerts: int
    open_loads: int
    fuel_cost_per_mile: Decimal