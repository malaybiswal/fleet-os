from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.driver import Driver
from app.models.dwell_event import DwellEvent
from app.models.fleet import Fleet
from app.models.load import Load
from app.models.truck import Truck
from app.repositories.facility_repository import FacilityRepository


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)

repo = FacilityRepository()


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def _create_fleet(db, name: str) -> Fleet:
    fleet = Fleet(name=name)
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    return fleet


def _create_load(db, fleet: Fleet, load_id: str) -> Load:
    truck = db.query(Truck).filter(Truck.fleet_id == fleet.id).first()
    if truck is None:
        truck = Truck(truck_id=f"TRK-{fleet.id}", fleet_id=fleet.id, status="moving")
        driver = Driver(driver_id=f"DRV-{fleet.id}", name="Test Driver", status="active", fleet_id=fleet.id)
        db.add_all([truck, driver])
        db.commit()
    load = Load(
        load_id=load_id,
        truck_id=f"TRK-{fleet.id}",
        driver_id=f"DRV-{fleet.id}",
        status="delivered",
        fleet_id=fleet.id,
    )
    db.add(load)
    db.commit()
    db.refresh(load)
    return load


def _create_dwell_event(
    db,
    fleet: Fleet,
    load: Load,
    facility_id: int | None = None,
    facility_name: str | None = None,
    arrival: datetime | None = None,
    dwell_hours: float = 1.0,
) -> DwellEvent:
    arrival = arrival or datetime(2026, 6, 1, 8, 0)
    event = DwellEvent(
        load_id=load.load_id,
        fleet_id=fleet.id,
        facility_id=facility_id,
        facility_name=facility_name,
        arrival_time=arrival,
        departure_time=arrival + timedelta(hours=dwell_hours),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def test_get_or_create_creates_then_reuses():
    db = TestingSessionLocal()
    fleet = _create_fleet(db, "Fleet A")

    first = repo.get_or_create(db, fleet.id, "Houston Crossdock")
    second = repo.get_or_create(db, fleet.id, "  houston   CROSSDOCK ")

    assert first.id == second.id
    assert first.name == "Houston Crossdock"
    assert first.normalized_name == "houston crossdock"
    db.close()


def test_get_or_create_is_fleet_scoped():
    db = TestingSessionLocal()
    fleet_a = _create_fleet(db, "Fleet A")
    fleet_b = _create_fleet(db, "Fleet B")

    a = repo.get_or_create(db, fleet_a.id, "Denver West DC")
    b = repo.get_or_create(db, fleet_b.id, "Denver West DC")

    assert a.id != b.id
    db.close()


def test_get_by_id_rejects_cross_fleet():
    db = TestingSessionLocal()
    fleet_a = _create_fleet(db, "Fleet A")
    fleet_b = _create_fleet(db, "Fleet B")
    facility = repo.get_or_create(db, fleet_a.id, "Dallas Mega Cold Storage")

    assert repo.get_by_id(db, fleet_a.id, facility.id) is not None
    assert repo.get_by_id(db, fleet_b.id, facility.id) is None
    db.close()


def test_dwell_rows_fleet_isolation_and_date_filter():
    db = TestingSessionLocal()
    fleet_a = _create_fleet(db, "Fleet A")
    fleet_b = _create_fleet(db, "Fleet B")
    facility_a = repo.get_or_create(db, fleet_a.id, "Atlanta Reload Hub")
    facility_b = repo.get_or_create(db, fleet_b.id, "Atlanta Reload Hub")

    load_a = _create_load(db, fleet_a, "LOAD-A1")
    load_b = _create_load(db, fleet_b, "LOAD-B1")
    _create_dwell_event(db, fleet_a, load_a, facility_id=facility_a.id, arrival=datetime(2026, 6, 1, 8, 0))
    _create_dwell_event(db, fleet_b, load_b, facility_id=facility_b.id, arrival=datetime(2026, 6, 1, 8, 0))

    rows = repo.dwell_rows_for_intelligence(db, fleet_a.id)
    assert len(rows) == 1
    facility, event = rows[0]
    assert facility.id == facility_a.id
    assert event.load_id == "LOAD-A1"

    rows = repo.dwell_rows_for_intelligence(db, fleet_a.id, start_date=datetime(2026, 6, 2))
    assert rows == []
    db.close()


def test_dwell_rows_include_unlinked_legacy_names():
    db = TestingSessionLocal()
    fleet = _create_fleet(db, "Fleet A")
    load = _create_load(db, fleet, "LOAD-A1")
    _create_dwell_event(db, fleet, load, facility_name="Legacy Yard")

    rows = repo.dwell_rows_for_intelligence(db, fleet.id)
    assert len(rows) == 1
    facility, event = rows[0]
    assert facility is None
    assert event.facility_name == "Legacy Yard"
    db.close()


def test_dwell_rows_skip_events_without_facility():
    db = TestingSessionLocal()
    fleet = _create_fleet(db, "Fleet A")
    load = _create_load(db, fleet, "LOAD-A1")
    _create_dwell_event(db, fleet, load, facility_id=None, facility_name=None)

    assert repo.dwell_rows_for_intelligence(db, fleet.id) == []
    db.close()
