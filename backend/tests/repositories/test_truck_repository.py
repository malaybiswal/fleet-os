from decimal import Decimal
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.truck import Truck
from app.repositories.truck_repository import TruckRepository


def test_truck_repository_create_get_update_position():
    db = SessionLocal()
    repo = TruckRepository()

    truck_id = "TEST-TRUCK-001"

    try:
        existing = repo.get_by_truck_id(db, truck_id)
        if existing:
            db.delete(existing)
            db.commit()

        truck = Truck(
            truck_id=truck_id,
            status="active",
            current_location="Austin, TX",
        )

        created = repo.create(db, truck)
        assert created.id is not None
        assert created.truck_id == truck_id

        fetched = repo.get_by_truck_id(db, truck_id)
        assert fetched is not None
        assert fetched.status == "active"

        updated = repo.update_position(
            db=db,
            truck_id=truck_id,
            lat=Decimal("30.267200"),
            lon=Decimal("-97.743100"),
            last_seen_at=datetime.now(timezone.utc),
        )

        assert updated is not None
        assert str(updated.current_lat) == "30.267200"
        assert str(updated.current_lon) == "-97.743100"
        assert updated.last_seen_at is not None

    finally:
        existing = repo.get_by_truck_id(db, truck_id)
        if existing:
            db.delete(existing)
            db.commit()
        db.close()