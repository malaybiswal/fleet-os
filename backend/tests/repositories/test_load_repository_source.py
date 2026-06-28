from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.fleet import Fleet
from app.models.load import Load
from app.repositories.load_repository import LoadRepository


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)

repo = LoadRepository()


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def _fleet(db, name: str) -> Fleet:
    fleet = Fleet(name=name)
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    return fleet


def _load(db, fleet_id, load_id, source, status="available"):
    load = Load(load_id=load_id, fleet_id=fleet_id, source=source, status=status)
    db.add(load)
    db.commit()
    return load


def test_delete_by_fleet_and_source_isolates_demo_and_other_fleets():
    db = TestingSessionLocal()
    try:
        fleet_a = _fleet(db, "Fleet A")
        fleet_b = _fleet(db, "Fleet B")
        _load(db, fleet_a.id, "demo:a:1", "demo")
        _load(db, fleet_a.id, "dat:a:1", "dat")
        _load(db, fleet_a.id, "dat:a:2", "dat")
        _load(db, fleet_b.id, "dat:b:1", "dat")

        deleted = repo.delete_by_fleet_and_source(db, fleet_id=fleet_a.id, source="dat")

        assert deleted == 2
        remaining = {load.load_id for load in db.query(Load).all()}
        assert remaining == {"demo:a:1", "dat:b:1"}
    finally:
        db.close()


def test_backfill_sets_null_source_to_demo_and_is_idempotent():
    """Mirrors migration e1a2b3c4d5e6: pre-DAT (NULL) rows become 'demo'."""
    db = TestingSessionLocal()
    try:
        fleet = _fleet(db, "Fleet")
        _load(db, fleet.id, "DEMO-LOAD-1", None)
        _load(db, fleet.id, "DEMO-LOAD-2", None)
        _load(db, fleet.id, "dat:f:1", "dat")

        backfill = text("UPDATE loads SET source = 'demo' WHERE source IS NULL")
        db.execute(backfill)
        db.commit()

        sources = {load.load_id: load.source for load in db.query(Load).all()}
        assert sources == {
            "DEMO-LOAD-1": "demo",
            "DEMO-LOAD-2": "demo",
            "dat:f:1": "dat",
        }

        # Idempotent: re-running touches nothing.
        assert db.execute(backfill).rowcount == 0
    finally:
        db.close()
