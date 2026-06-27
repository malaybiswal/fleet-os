from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.fleet import get_current_fleet_id
from app.jobs.dat_load_ingestion import ingest_dat_loads
from app.schemas.integration import (
    DatConnectionTestResponse,
    DatCredentialRequest,
    DatIntegrationStatus,
    DatSyncAccepted,
)
from app.services.integration_service import IntegrationNotFoundError, IntegrationService


router = APIRouter(prefix="/api/integrations", tags=["integrations"])
integration_service = IntegrationService()


@router.get("/dat", response_model=DatIntegrationStatus)
def get_dat_integration(
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
):
    integration = integration_service.get_dat_status(db, fleet_id=fleet_id)
    return _status_response(integration)


@router.put("/dat", response_model=DatIntegrationStatus)
def connect_dat_integration(
    payload: DatCredentialRequest,
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
):
    integration = integration_service.set_dat_credentials(
        db,
        fleet_id=fleet_id,
        credentials=payload.model_dump(),
    )
    return _status_response(integration)


@router.post("/dat/test", response_model=DatConnectionTestResponse)
def test_dat_integration(
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
):
    try:
        integration_service.test_dat_connection(db, fleet_id=fleet_id)
    except IntegrationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DatConnectionTestResponse(success=True, message="DAT connection succeeded")


@router.post("/dat/sync", response_model=DatSyncAccepted, status_code=202)
def sync_dat_integration(
    background_tasks: BackgroundTasks,
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
):
    integration = integration_service.get_dat_status(db, fleet_id=fleet_id)
    if integration is None or integration.status == "disabled":
        raise HTTPException(status_code=404, detail="DAT integration is not connected")

    # Run the sync off the request path so network/token/rate-limit failures
    # against live DAT never block this request or the frontend. Progress is
    # observable via GET /dat (last_sync_at / last_error).
    background_tasks.add_task(ingest_dat_loads, fleet_id=fleet_id)
    return DatSyncAccepted(status="accepted", detail="DAT sync started")


@router.delete("/dat", response_model=DatIntegrationStatus)
def disconnect_dat_integration(
    fleet_id: int = Depends(get_current_fleet_id),
    db: Session = Depends(get_db),
):
    try:
        integration = integration_service.disconnect_dat(db, fleet_id=fleet_id)
    except IntegrationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _status_response(integration)


def _status_response(integration) -> DatIntegrationStatus:
    if integration is None:
        return DatIntegrationStatus(
            connected=False,
            status="not_connected",
        )

    connected = integration.status in {"connected", "error"}
    config = (
        integration_service.public_dat_config(integration) if connected else {}
    )
    return DatIntegrationStatus(
        connected=connected,
        status=integration.status,
        last_sync_at=integration.last_sync_at,
        last_error=integration.last_error,
        service_account_email=config.get("service_account_email"),
        user_email=config.get("user_email"),
        base_url=config.get("base_url"),
        filters=config.get("filters") or {},
    )
