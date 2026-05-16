from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import DashboardService
from app.dependencies.fleet import get_current_fleet_id

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_dashboard_service() -> DashboardService:
    return DashboardService()


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
):
    return service.get_summary(
        db=db,
        fleet_id=fleet_id,
        start_date=start_date,
        end_date=end_date,
    )