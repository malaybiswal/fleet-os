from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.fleet import get_current_fleet_id
from app.schemas.dispatcher_command_center import (
    DispatcherAssignmentRequest,
    DispatcherCommandCenterDecision,
)
from app.schemas.load import LoadResponse
from app.services.dispatcher_command_center_service import (
    DispatcherAssignmentConflictError,
    DispatcherCommandCenterService,
    InvalidLoadEconomicsError,
)

router = APIRouter(
    prefix="/api/dispatcher-command-center",
    tags=["dispatcher-command-center"],
)

dispatcher_command_center_service = DispatcherCommandCenterService()


@router.get(
    "/candidates",
    response_model=list[LoadResponse],
)
def get_candidate_loads(
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
):
    return dispatcher_command_center_service.get_candidate_loads(db=db, fleet_id=fleet_id)


@router.get(
    "/loads/{load_id}/decision",
    response_model=DispatcherCommandCenterDecision,
)
def get_load_decision(
    load_id: str,
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
):
    try:
        decision = dispatcher_command_center_service.get_load_decision(
            db=db,
            fleet_id=fleet_id,
            load_id=load_id,
        )
    except InvalidLoadEconomicsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if decision is None:
        raise HTTPException(
            status_code=404,
            detail=f"Load {load_id} not found",
        )

    return decision


@router.post(
    "/loads/{load_id}/assign",
    response_model=LoadResponse,
)
def accept_recommendation(
    load_id: str,
    request: DispatcherAssignmentRequest,
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
):
    try:
        load = dispatcher_command_center_service.accept_recommendation(
            db=db,
            fleet_id=fleet_id,
            load_id=load_id,
            truck_id=request.truck_id,
            driver_id=request.driver_id,
        )
    except InvalidLoadEconomicsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DispatcherAssignmentConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if load is None:
        raise HTTPException(
            status_code=404,
            detail=f"Load {load_id} not found",
        )

    return load
