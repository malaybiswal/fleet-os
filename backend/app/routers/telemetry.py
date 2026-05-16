from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.telemetry_event import TelemetryEvent
from app.schemas.telemetry_event import TelemetryEventCreate, TelemetryEventResponse
from app.services.telemetry_service import TelemetryService
from app.dependencies.fleet import get_current_fleet_id

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


def get_telemetry_service() -> TelemetryService:
    return TelemetryService()


@router.post(
    "",
    response_model=TelemetryEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_telemetry(
    payload: TelemetryEventCreate,
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
    service: TelemetryService = Depends(get_telemetry_service),
):
    telemetry_event = TelemetryEvent(**payload.model_dump())
    return service.ingest_telemetry(
        db=db,
        telemetry_event=telemetry_event,
        fleet_id=fleet_id,
    )


@router.get("/{truck_id}", response_model=list[TelemetryEventResponse])
def get_telemetry_for_truck(
    truck_id: str,
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
    service: TelemetryService = Depends(get_telemetry_service),
):
    return service.get_telemetry_for_truck(
        db=db,
        truck_id=truck_id,
        fleet_id=fleet_id,
        limit=limit,
        offset=offset,
    )