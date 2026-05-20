from datetime import date

from sqlalchemy.orm import Session

from app.models import Carrier, CarrierSnapshot
from app.schemas import CarrierCreate


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
