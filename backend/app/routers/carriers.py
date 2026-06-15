"""
TASK-026 - Carrier API Layer
"""

from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import carrier_repository
from app.schemas.carrier import (
    CarrierListItem,
    CarrierPipelineStats,
    CarrierRead,
    CarrierStatsResponse,
    LogContactRequest,
    OutreachNoteCreate,
    OutreachNoteRead,
    OutreachNoteUpdate,
    OutreachStatusUpdate,
    PaginatedResponse,
    TagAddRequest,
    TagCreate,
    TagRead,
)

router = APIRouter(prefix="/api/carriers", tags=["carriers"])
tags_router = APIRouter(prefix="/api/tags", tags=["tags"])

CarrierOrderBy = Literal[
    "lead_score_desc",
    "authority_date_desc",
    "power_units_desc",
    "created_at_desc",
    "id_asc",
]


# ---------------------------------------------------------------------------
# Static routes FIRST (before /{carrier_id})
# ---------------------------------------------------------------------------


@router.get("/pipeline-stats", response_model=CarrierPipelineStats)
def get_pipeline_stats(db: Session = Depends(get_db)):
    return carrier_repository.get_pipeline_stats(db)


@router.get("/search", response_model=PaginatedResponse[CarrierListItem])
def search_carriers(
    q: str = Query(..., min_length=2, description="Search term"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    results, total = carrier_repository.search_carriers(
        db,
        query=q,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(data=results, total=total, page=page, page_size=page_size)


@router.get("/new", response_model=PaginatedResponse[CarrierListItem])
def list_new_carriers(
    days: int = Query(
        30,
        ge=1,
        le=365,
        description="Carriers added within this many days",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    carriers, total = carrier_repository.list_carriers(
        db,
        created_after=since,
        page=page,
        page_size=page_size,
        order_by="created_at_desc",
    )
    return PaginatedResponse(data=carriers, total=total, page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[CarrierListItem])
def list_carriers(
    state: Optional[str] = Query(None, max_length=2),
    min_fleet: Optional[int] = Query(None, ge=0),
    max_fleet: Optional[int] = Query(None, ge=0),
    power_units_min: Optional[int] = Query(None, ge=0),
    power_units_max: Optional[int] = Query(None, ge=0),
    authority_age_days: Optional[int] = Query(None, ge=0),
    authority_status: Optional[str] = None,
    outreach_status: Optional[str] = None,
    tag: Optional[str] = None,
    cargo_type: Optional[str] = None,
    order_by: CarrierOrderBy = Query("lead_score_desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    resolved_power_units_min = (
        power_units_min if power_units_min is not None else min_fleet
    )
    resolved_power_units_max = (
        power_units_max if power_units_max is not None else max_fleet
    )
    if (
        resolved_power_units_min is not None
        and resolved_power_units_max is not None
        and resolved_power_units_min > resolved_power_units_max
    ):
        raise HTTPException(
            status_code=422,
            detail="power_units_min must be less than or equal to power_units_max",
        )

    carriers, total = carrier_repository.list_carriers(
        db,
        state=state,
        power_units_min=resolved_power_units_min,
        power_units_max=resolved_power_units_max,
        authority_age_days=authority_age_days,
        authority_status=authority_status,
        outreach_status=outreach_status,
        tag=tag,
        cargo_type=cargo_type,
        order_by=order_by,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(data=carriers, total=total, page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# Single carrier - AFTER static routes
# ---------------------------------------------------------------------------


@router.get("/{carrier_id}", response_model=CarrierRead)
def get_carrier(carrier_id: int, db: Session = Depends(get_db)):
    carrier = carrier_repository.get_carrier(db, carrier_id)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    return carrier


# ---------------------------------------------------------------------------
# Outreach status
# ---------------------------------------------------------------------------


@router.patch("/{carrier_id}/outreach-status", response_model=CarrierRead)
def update_outreach_status(
    carrier_id: int,
    payload: OutreachStatusUpdate,
    db: Session = Depends(get_db),
):
    carrier = carrier_repository.get_carrier(db, carrier_id)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    carrier.outreach_status = payload.status.value
    db.commit()
    db.refresh(carrier)
    return carrier


# ---------------------------------------------------------------------------
# Log contact (outreach workflow action)
# ---------------------------------------------------------------------------


@router.post("/{carrier_id}/log-contact", response_model=CarrierRead)
def log_contact(
    carrier_id: int,
    payload: LogContactRequest,
    db: Session = Depends(get_db),
):
    carrier = carrier_repository.log_contact(db, carrier_id=carrier_id, data=payload)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    return carrier


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------


@router.get("/{carrier_id}/notes", response_model=list[OutreachNoteRead])
def list_notes(carrier_id: int, db: Session = Depends(get_db)):
    carrier = carrier_repository.get_carrier(db, carrier_id)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    return sorted(carrier.outreach_notes, key=lambda n: n.created_at, reverse=True)


@router.post("/{carrier_id}/notes", response_model=OutreachNoteRead, status_code=201)
def create_note(
    carrier_id: int,
    payload: OutreachNoteCreate,
    db: Session = Depends(get_db),
):
    carrier = carrier_repository.get_carrier(db, carrier_id)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    return carrier_repository.create_note(db, carrier_id=carrier_id, data=payload)


@router.patch("/{carrier_id}/notes/{note_id}", response_model=OutreachNoteRead)
def update_note(
    carrier_id: int,
    note_id: int,
    payload: OutreachNoteUpdate,
    db: Session = Depends(get_db),
):
    note = carrier_repository.update_note(db, note_id=note_id, data=payload)
    if not note or note.carrier_id != carrier_id:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{carrier_id}/notes/{note_id}", status_code=204)
def delete_note(carrier_id: int, note_id: int, db: Session = Depends(get_db)):
    deleted = carrier_repository.delete_note(
        db,
        note_id=note_id,
        carrier_id=carrier_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


@router.get("/{carrier_id}/tags", response_model=list[TagRead])
def list_carrier_tags(carrier_id: int, db: Session = Depends(get_db)):
    carrier = carrier_repository.get_carrier(db, carrier_id)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    return carrier.tags


@router.post("/{carrier_id}/tags", response_model=list[TagRead], status_code=201)
def add_tag(
    carrier_id: int,
    payload: TagAddRequest,
    db: Session = Depends(get_db),
):
    carrier = carrier_repository.get_carrier(db, carrier_id)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    added = carrier_repository.add_tag_to_carrier(
        db,
        carrier_id=carrier_id,
        tag_id=payload.tag_id,
    )
    if not added:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.refresh(carrier)
    return carrier.tags


@router.delete("/{carrier_id}/tags/{tag_id}", status_code=204)
def remove_tag(carrier_id: int, tag_id: int, db: Session = Depends(get_db)):
    removed = carrier_repository.remove_tag_from_carrier(
        db,
        carrier_id=carrier_id,
        tag_id=tag_id,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Tag association not found")


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@router.get("/{carrier_id}/stats", response_model=CarrierStatsResponse)
def get_carrier_stats(carrier_id: int, db: Session = Depends(get_db)):
    carrier = carrier_repository.get_carrier(db, carrier_id)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    snapshots = carrier_repository.get_carrier_snapshots(db, carrier_id=carrier_id)
    return CarrierStatsResponse(carrier_id=carrier_id, snapshots=snapshots)


# ---------------------------------------------------------------------------
# Global tags
# ---------------------------------------------------------------------------


@tags_router.get("", response_model=list[TagRead])
def list_tags(db: Session = Depends(get_db)):
    return carrier_repository.list_tags(db)


@tags_router.post("", response_model=TagRead, status_code=201)
def create_tag(payload: TagCreate, db: Session = Depends(get_db)):
    return carrier_repository.create_tag(db, name=payload.name)
