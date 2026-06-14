from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.fleet import get_current_fleet_id
from app.schemas.facility import FacilityDetail, FacilityIntelligence
from app.services.facility_service import SORT_FIELDS, FacilityService

router = APIRouter(prefix="/api/facilities", tags=["facilities"])


def get_facility_service() -> FacilityService:
    return FacilityService()


@router.get(
    "",
    response_model=list[FacilityIntelligence],
)
def list_facilities(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    sort: str = Query(default="operational_score", enum=sorted(SORT_FIELDS)),
    order: str = Query(default="asc", enum=["asc", "desc"]),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    fleet_id: int = Depends(get_current_fleet_id),
    service: FacilityService = Depends(get_facility_service),
):
    return service.list_facility_intelligence(
        db=db,
        fleet_id=fleet_id,
        start_date=start_date,
        end_date=end_date,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{facility_id}",
    response_model=FacilityDetail,
)
def get_facility(
    facility_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    fleet_id: int = Depends(get_current_fleet_id),
    service: FacilityService = Depends(get_facility_service),
):
    return service.get_facility_detail(
        db=db,
        fleet_id=fleet_id,
        facility_id=facility_id,
        start_date=start_date,
        end_date=end_date,
    )
