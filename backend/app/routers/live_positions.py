from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.fleet import get_current_fleet_id
from app.schemas.live_position import LiveTruckPosition
from app.services.live_position_service import get_live_positions_for_fleet

router = APIRouter(prefix="/api/fleet", tags=["fleet"])


@router.get("/live-positions", response_model=list[LiveTruckPosition])
def get_live_positions(
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
):
    return get_live_positions_for_fleet(db, fleet_id)
