from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import case, delete, func, or_
from sqlalchemy.orm import Session

from app.schemas.carrier import CarrierPipelineStats

from app.models import Carrier, CarrierSnapshot, OutreachNote, Tag
from app.models.carrier import carrier_tags
from app.schemas import CarrierCreate
from app.schemas.carrier import OutreachNoteCreate, OutreachNoteUpdate


def upsert_carrier(db: Session, carrier_create: CarrierCreate) -> Carrier:
    carrier = (
        db.query(Carrier)
        .filter(Carrier.dot_number == carrier_create.dot_number)
        .one_or_none()
    )
    values = carrier_create.model_dump()

    if carrier is None:
        carrier = Carrier(**values)
        db.add(carrier)
    else:
        for field_name, value in values.items():
            setattr(carrier, field_name, value)

    db.flush()
    return carrier


def upsert_carrier_snapshot(
    db: Session,
    *,
    carrier: Carrier,
    snapshot_date: date,
    raw_payload: dict,
) -> CarrierSnapshot:
    snapshot = (
        db.query(CarrierSnapshot)
        .filter(
            CarrierSnapshot.carrier_id == carrier.id,
            CarrierSnapshot.snapshot_date == snapshot_date,
        )
        .one_or_none()
    )
    values = {
        "power_units": carrier.power_units,
        "driver_count": carrier.driver_count,
        "authority_status": carrier.authority_status,
        "cargo_types": carrier.cargo_types,
        "raw_payload": raw_payload,
    }

    if snapshot is None:
        snapshot = CarrierSnapshot(
            carrier_id=carrier.id,
            snapshot_date=snapshot_date,
            **values,
        )
        db.add(snapshot)
    else:
        for field_name, value in values.items():
            setattr(snapshot, field_name, value)

    db.flush()
    return snapshot


def list_carriers(
    db: Session,
    *,
    state: Optional[str] = None,
    power_units_min: Optional[int] = None,
    power_units_max: Optional[int] = None,
    authority_age_days: Optional[int] = None,
    authority_status: Optional[str] = None,
    outreach_status: Optional[str] = None,
    tag: Optional[str] = None,
    created_after: Optional[datetime] = None,
    order_by: str = "id_asc",
    page: int = 1,
    page_size: int = 50,
) -> tuple[List[Carrier], int]:
    query = db.query(Carrier)

    if state:
        query = query.filter(Carrier.state == state.upper())
    if power_units_min is not None:
        query = query.filter(Carrier.power_units >= power_units_min)
    if power_units_max is not None:
        query = query.filter(Carrier.power_units <= power_units_max)
    if authority_age_days is not None:
        cutoff = date.today() - timedelta(days=authority_age_days)
        query = query.filter(Carrier.authority_date >= cutoff)
    if authority_status:
        query = query.filter(Carrier.authority_status == authority_status)
    if outreach_status:
        query = query.filter(Carrier.outreach_status == outreach_status)
    if tag:
        query = query.join(Carrier.tags).filter(Tag.name == tag.strip().lower())
    if created_after:
        query = query.filter(Carrier.created_at >= created_after)

    total = query.count()

    if order_by == "created_at_desc":
        query = query.order_by(Carrier.created_at.desc())
    else:
        query = query.order_by(Carrier.id.asc())

    carriers = query.offset((page - 1) * page_size).limit(page_size).all()
    return carriers, total


def get_carrier(db: Session, carrier_id: int) -> Optional[Carrier]:
    return db.query(Carrier).filter(Carrier.id == carrier_id).first()


SIMILARITY_THRESHOLD = 0.35


def search_carriers(
    db: Session,
    query: str,
    page: int = 1,
    page_size: int = 50,
) -> tuple[List[Carrier], int]:
    prefix = f"{query}%"
    substring = f"%{query}%"

    # word_similarity(needle, haystack) — scores the query against the best-matching
    # word portion of the company name, which is far more accurate than whole-string
    # similarity for short queries against long carrier names.
    legal_similarity = func.word_similarity(query, Carrier.legal_name)
    dba_similarity = func.word_similarity(query, func.coalesce(Carrier.dba_name, ""))
    best_similarity = func.greatest(legal_similarity, dba_similarity)

    # Rank 1: exact DOT
    # Rank 2: exact MC
    # Rank 3: prefix match on legal_name or dba_name
    # Rank 4: substring match on legal_name, dba_name, or city
    # Rank 5: fuzzy trigram match on legal_name (typo tolerance)
    rank_expr = case(
        (Carrier.dot_number == query, 1),
        (Carrier.mc_number == query, 2),
        (or_(Carrier.legal_name.ilike(prefix), Carrier.dba_name.ilike(prefix)), 3),
        (
            or_(
                Carrier.legal_name.ilike(substring),
                Carrier.dba_name.ilike(substring),
                Carrier.city.ilike(substring),
            ),
            4,
        ),
        else_=5,
    )

    search_query = db.query(Carrier).filter(
        or_(
            Carrier.dot_number == query,
            Carrier.mc_number == query,
            Carrier.legal_name.ilike(substring),
            Carrier.dba_name.ilike(substring),
            Carrier.city.ilike(substring),
            best_similarity > SIMILARITY_THRESHOLD,
        )
    )

    total = search_query.count()
    carriers = (
        search_query
        .order_by(rank_expr, best_similarity.desc(), Carrier.legal_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return carriers, total


def get_carrier_snapshots(db: Session, carrier_id: int) -> List[CarrierSnapshot]:
    return (
        db.query(CarrierSnapshot)
        .filter(CarrierSnapshot.carrier_id == carrier_id)
        .order_by(CarrierSnapshot.snapshot_date.asc())
        .all()
    )


def create_note(
    db: Session,
    carrier_id: int,
    data: OutreachNoteCreate,
) -> OutreachNote:
    values = data.model_dump(exclude_unset=True)
    content = values.pop("content")
    values.pop("carrier_id", None)
    note = OutreachNote(carrier_id=carrier_id, note=content, **values)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def update_note(
    db: Session,
    note_id: int,
    data: OutreachNoteUpdate,
) -> Optional[OutreachNote]:
    note = db.query(OutreachNote).filter(OutreachNote.id == note_id).first()
    if not note:
        return None

    values = data.model_dump(exclude_unset=True)
    if "content" in values:
        values["note"] = values.pop("content")

    for field, value in values.items():
        setattr(note, field, value)

    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note_id: int, carrier_id: int) -> bool:
    note = (
        db.query(OutreachNote)
        .filter(OutreachNote.id == note_id, OutreachNote.carrier_id == carrier_id)
        .first()
    )
    if not note:
        return False

    db.delete(note)
    db.commit()
    return True


def get_pipeline_stats(db: Session) -> CarrierPipelineStats:
    since = datetime.utcnow() - timedelta(days=30)
    total = db.query(func.count(Carrier.id)).scalar() or 0
    new_last_30_days = (
        db.query(func.count(Carrier.id))
        .filter(Carrier.created_at >= since)
        .scalar()
        or 0
    )
    not_contacted = (
        db.query(func.count(Carrier.id))
        .filter(Carrier.outreach_status == "not_contacted")
        .scalar()
        or 0
    )
    return CarrierPipelineStats(
        total=total,
        new_last_30_days=new_last_30_days,
        avg_lead_score=None,
        not_contacted=not_contacted,
    )


def list_tags(db: Session) -> List[Tag]:
    return db.query(Tag).order_by(Tag.name.asc()).all()


def create_tag(db: Session, name: str) -> Tag:
    tag = Tag(name=name.strip().lower())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def add_tag_to_carrier(db: Session, carrier_id: int, tag_id: int) -> bool:
    carrier = get_carrier(db, carrier_id)
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not carrier or not tag:
        return False
    if tag not in carrier.tags:
        carrier.tags.append(tag)
        db.commit()
    return True


def remove_tag_from_carrier(db: Session, carrier_id: int, tag_id: int) -> bool:
    result = db.execute(
        delete(carrier_tags).where(
            carrier_tags.c.carrier_id == carrier_id,
            carrier_tags.c.tag_id == tag_id,
        )
    )
    db.commit()
    return result.rowcount > 0
