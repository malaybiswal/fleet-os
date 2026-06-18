from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base
from app.models.alert import Alert
from app.models.driver import Driver
from app.models.dwell_event import DwellEvent
from app.models.fleet import Fleet
from app.models.load import Load
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.models.user import User
from app.seed.demo_dataset import build_demo_dataset
from app.seed.mock_fleets import DEMO_FLEET_NAMES
from app.seed.persist import (
    count_demo_data,
    dry_run_demo_environment,
    reset_demo_environment,
)


BASE_DATE = datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_reset_preserves_non_demo_data(db):
    _insert_non_demo_rows(db)

    result = reset_demo_environment(db, seed=32032, base_date=BASE_DATE)

    assert result.created == build_demo_dataset(seed=32032, base_date=BASE_DATE).counts()
    assert db.query(Fleet).filter(Fleet.name == "Local Fleet").count() == 1
    assert db.query(Truck).filter(Truck.truck_id == "LOCAL-TRUCK-001").count() == 1
    assert db.query(Load).filter(Load.load_id == "LOCAL-LOAD-001").count() == 1


def test_seeded_demo_rows_have_valid_relationships_and_fleet_scope(db):
    reset_demo_environment(db, seed=32032, base_date=BASE_DATE)

    trucks_by_id = {truck.truck_id: truck for truck in db.query(Truck).all()}
    drivers_by_id = {driver.driver_id: driver for driver in db.query(Driver).all()}
    loads_by_id = {load.load_id: load for load in db.query(Load).all()}

    for load in db.query(Load).all():
        assert load.truck_id in trucks_by_id
        assert load.driver_id in drivers_by_id
        assert load.fleet_id == trucks_by_id[load.truck_id].fleet_id
        assert load.fleet_id == drivers_by_id[load.driver_id].fleet_id

    for dwell_event in db.query(DwellEvent).all():
        assert dwell_event.load_id in loads_by_id
        assert dwell_event.fleet_id == loads_by_id[dwell_event.load_id].fleet_id

    for telemetry_event in db.query(TelemetryEvent).all():
        assert telemetry_event.truck_id in trucks_by_id
        assert telemetry_event.fleet_id == trucks_by_id[telemetry_event.truck_id].fleet_id

    for alert in db.query(Alert).all():
        assert alert.truck_id in trucks_by_id
        assert alert.fleet_id == trucks_by_id[alert.truck_id].fleet_id


def test_reset_demo_environment_is_idempotent(db):
    first = reset_demo_environment(db, seed=32032, base_date=BASE_DATE)
    first_counts = count_demo_data(db)

    second = reset_demo_environment(db, seed=32032, base_date=BASE_DATE)
    second_counts = count_demo_data(db)

    assert first_counts == second_counts
    # Alerts and users are not part of dataset.counts(): alerts are derived by
    # alert evaluation at seed time; users are created by assign_demo_users.
    excluded = {"alerts", "users"}
    deleted_without_derived = {k: v for k, v in second.deleted.items() if k not in excluded}
    assert deleted_without_derived == first.created
    assert second_counts == build_demo_dataset(seed=32032, base_date=BASE_DATE).counts()


def test_reset_preserves_users_referencing_demo_fleets(db):
    reset_demo_environment(db, seed=32032, base_date=BASE_DATE)
    operations_fleet = (
        db.query(Fleet)
        .filter(Fleet.name == DEMO_FLEET_NAMES[0])
        .one()
    )
    user = User(
        firebase_uid="demo-user",
        email="demo@fleetos.local",
        name="Demo User",
        fleet_id=operations_fleet.id,
        role="admin",
    )
    db.add(user)
    db.commit()

    result = reset_demo_environment(db, seed=32032, base_date=BASE_DATE)
    db.refresh(user)

    assert result.deleted["fleets"] == 1
    assert user.fleet_id == operations_fleet.id
    assert db.query(User).filter(User.firebase_uid == "demo-user").count() == 1
    assert count_demo_data(db) == build_demo_dataset(
        seed=32032,
        base_date=BASE_DATE,
    ).counts()


def test_dry_run_reports_only_unreferenced_demo_fleets_as_deletable(db):
    reset_demo_environment(db, seed=32032, base_date=BASE_DATE)
    operations_fleet = (
        db.query(Fleet)
        .filter(Fleet.name == DEMO_FLEET_NAMES[0])
        .one()
    )
    db.add(
        User(
            firebase_uid="demo-user",
            email="demo@fleetos.local",
            name="Demo User",
            fleet_id=operations_fleet.id,
            role="admin",
        )
    )
    db.commit()

    result = dry_run_demo_environment(db, seed=32032, base_date=BASE_DATE)

    assert result.deleted["fleets"] == 1
    assert count_demo_data(db) == build_demo_dataset(
        seed=32032,
        base_date=BASE_DATE,
    ).counts()


def _insert_non_demo_rows(db):
    fleet = Fleet(name="Local Fleet")
    db.add(fleet)
    db.flush()

    truck = Truck(
        truck_id="LOCAL-TRUCK-001",
        fleet_id=fleet.id,
        status="moving",
        current_location="Austin, TX",
    )
    driver = Driver(
        driver_id="LOCAL-DRIVER-001",
        fleet_id=fleet.id,
        name="Local Driver",
        status="available",
    )
    db.add_all([truck, driver])
    db.flush()

    load = Load(
        load_id="LOCAL-LOAD-001",
        fleet_id=fleet.id,
        truck_id=truck.truck_id,
        driver_id=driver.driver_id,
        broker_name="Local Broker",
        origin="Austin, TX",
        destination="Dallas, TX",
        revenue=Decimal("1000"),
        miles=Decimal("200"),
        deadhead_miles=Decimal("15"),
        fuel_cost=Decimal("125"),
        maintenance_reserve=Decimal("50"),
        driver_cost=Decimal("300"),
        tolls=Decimal("20"),
        pickup_time=BASE_DATE,
        delivery_time=BASE_DATE,
        status="booked",
    )
    db.add(load)
    db.commit()
