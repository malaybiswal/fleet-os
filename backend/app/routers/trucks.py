from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.truck import TruckResponse
from app.services.truck_service import TruckService
from app.dependencies.fleet import get_current_fleet_id

router = APIRouter(prefix="/api/trucks", tags=["trucks"])


def get_truck_service() -> TruckService:
    return TruckService()


@router.get("", response_model=list[TruckResponse])
def list_trucks(
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
    service: TruckService = Depends(get_truck_service),
):
    return service.get_all_trucks(db, fleet_id)