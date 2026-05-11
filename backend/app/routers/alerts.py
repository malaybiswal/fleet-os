from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertResponse

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def get_alert_repository() -> AlertRepository:
    return AlertRepository()


@router.get("", response_model=list[AlertResponse])
def list_alerts(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    resolved: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    repository: AlertRepository = Depends(get_alert_repository),
):
    return repository.get_all(
        db=db,
        limit=limit,
        offset=offset,
        resolved=resolved,
    )


@router.patch("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    repository: AlertRepository = Depends(get_alert_repository),
):
    alert = repository.resolve(db=db, alert_id=alert_id)

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail=f"Alert {alert_id} not found",
        )

    return alert