from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dwell_event import DwellEvent
from app.schemas.dwell_event import (
    BrokerScorecard,
    DwellEventCreate,
    DwellEventResponse,
    FacilityScorecard,
)
from app.services.dwell_service import DwellService
from app.dependencies.fleet import get_current_fleet_id

router = APIRouter(prefix="/api/dwell", tags=["dwell"])


def get_dwell_service() -> DwellService:
    return DwellService()


@router.post(
    "",
    response_model=DwellEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dwell_event(
    payload: DwellEventCreate,
    truck_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    service: DwellService = Depends(get_dwell_service),
):
    dwell_event = DwellEvent(**payload.model_dump())
    return service.create_dwell_event(
        db=db,
        dwell_event=dwell_event,
        truck_id=truck_id,
    )


@router.get(
    "/events",
    response_model=list[DwellEventResponse],
)
def list_dwell_events(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    fleet_id: int = Depends(get_current_fleet_id),
    service: DwellService = Depends(get_dwell_service),
):
    return service.get_events(db=db, fleet_id=fleet_id, limit=limit, offset=offset)


@router.get(
    "/facility-scorecard",
    response_model=list[FacilityScorecard],
)
def get_facility_scorecard(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    fleet_id: int = Depends(get_current_fleet_id),
    service: DwellService = Depends(get_dwell_service),
):
    return service.get_facility_scorecard(
        db=db,
        fleet_id=fleet_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/broker-scorecard",
    response_model=list[BrokerScorecard],
)
def get_broker_scorecard(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    fleet_id: int = Depends(get_current_fleet_id),
    service: DwellService = Depends(get_dwell_service),
):
    return service.get_broker_scorecard(
        db=db,
        fleet_id=fleet_id,
        start_date=start_date,
        end_date=end_date,
    )