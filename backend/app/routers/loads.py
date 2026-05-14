from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.load import (
    LoadCreate,
    LoadProfitability,
    LoadResponse,
)
from app.services.load_service import LoadService

router = APIRouter(
    prefix="/api/loads",
    tags=["loads"],
)

load_service = LoadService()


@router.post("", response_model=LoadResponse)
def create_load(
    payload: LoadCreate,
    db: Session = Depends(get_db),
):
    return load_service.create_load(db, payload)


@router.get("", response_model=list[LoadResponse])
def get_loads(
    db: Session = Depends(get_db),
):
    return load_service.get_loads(db)


@router.get("/{load_id}/profitability", response_model=LoadProfitability)
def get_profitability(
    load_id: str,
    db: Session = Depends(get_db),
):
    result = load_service.get_profitability(db, load_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Load {load_id} not found",
        )

    return result