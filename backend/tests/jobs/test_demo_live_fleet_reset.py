from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base
from app.jobs import demo_live_fleet_reset
from app.models.alert import Alert
from app.models.driver import Driver
from app.models.dwell_event import DwellEvent
from app.models.fleet import Fleet
from app.models.load import Load
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.models.user import User


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


def test_reset_live_fleet_deletes_operational_rows_for_selected_fleet(db):
    live_fleet_id = _insert_live_fleet_rows(db, "live", 1)
    other_fleet_id = _insert_live_fleet_rows(db, "other", 2)

    result = demo_live_fleet_reset.reset_live_fleet_data(
        db,
        fleet_id=live_fleet_id,
    )

    assert result.fleet_id == live_fleet_id
    assert result.deleted == {
        "alerts": 1,
        "telemetry_events": 1,
        "dwell_events": 1,
        "loads": 1,
        "drivers": 1,
        "trucks": 1,
    }
    assert db.query(Fleet).filter(Fleet.id == live_fleet_id).count() == 1
    assert db.query(User).filter(User.fleet_id == live_fleet_id).count() == 1
    assert _counts_for_fleet(db, live_fleet_id) == {
        "alerts": 0,
        "telemetry_events": 0,
        "dwell_events": 0,
        "loads": 0,
        "drivers": 0,
        "trucks": 0,
    }
    assert _counts_for_fleet(db, other_fleet_id) == {
        "alerts": 1,
        "telemetry_events": 1,
        "dwell_events": 1,
        "loads": 1,
        "drivers": 1,
        "trucks": 1,
    }


def test_reset_live_fleet_deletes_related_rows_missing_fleet_id(db):
    live_fleet_id = _insert_live_fleet_rows(db, "live", 1)

    db.query(Alert).filter(Alert.fleet_id == live_fleet_id).update(
        {"fleet_id": None},
        synchronize_session=False,
    )
    db.query(TelemetryEvent).filter(TelemetryEvent.fleet_id == live_fleet_id).update(
        {"fleet_id": None},
        synchronize_session=False,
    )
    db.query(DwellEvent).filter(DwellEvent.fleet_id == live_fleet_id).update(
        {"fleet_id": None},
        synchronize_session=False,
    )
    db.query(Load).filter(Load.fleet_id == live_fleet_id).update(
        {"fleet_id": None},
        synchronize_session=False,
    )
    db.commit()

    result = demo_live_fleet_reset.reset_live_fleet_data(
        db,
        fleet_id=live_fleet_id,
    )

    assert result.deleted == {
        "alerts": 1,
        "telemetry_events": 1,
        "dwell_events": 1,
        "loads": 1,
        "drivers": 1,
        "trucks": 1,
    }
    assert db.query(Truck).filter(Truck.fleet_id == live_fleet_id).count() == 0


def test_reset_live_fleet_deletes_stale_source_trucks_from_old_fleets(db):
    live_fleet_id = _insert_live_fleet_rows(db, "live", 1)
    stale_fleet_id = _insert_live_fleet_rows(db, "stale", 2)
    db.query(Truck).filter(Truck.fleet_id == stale_fleet_id).update(
        {"truck_id": "SIM-001"},
        synchronize_session=False,
    )
    db.query(TelemetryEvent).filter(TelemetryEvent.fleet_id == stale_fleet_id).update(
        {"truck_id": "SIM-001"},
        synchronize_session=False,
    )
    db.query(Alert).filter(Alert.fleet_id == stale_fleet_id).update(
        {"truck_id": "SIM-001"},
        synchronize_session=False,
    )
    db.query(Load).filter(Load.fleet_id == stale_fleet_id).delete(
        synchronize_session=False,
    )
    db.query(DwellEvent).filter(DwellEvent.fleet_id == stale_fleet_id).delete(
        synchronize_session=False,
    )
    db.commit()

    result = demo_live_fleet_reset.reset_live_fleet_data(
        db,
        fleet_id=live_fleet_id,
    )

    assert result.deleted["trucks"] == 2
    assert db.query(Truck).filter(Truck.truck_id == "SIM-001").count() == 0


def test_reset_live_fleet_dry_run_reports_counts_without_deleting(db):
    live_fleet_id = _insert_live_fleet_rows(db, "live", 1)

    result = demo_live_fleet_reset.reset_live_fleet_data(
        db,
        fleet_id=live_fleet_id,
        dry_run=True,
    )

    assert result.dry_run is True
    assert result.deleted == {
        "alerts": 1,
        "telemetry_events": 1,
        "dwell_events": 1,
        "loads": 1,
        "drivers": 1,
        "trucks": 1,
    }
    assert _counts_for_fleet(db, live_fleet_id) == result.deleted


def test_resolve_live_fleet_id_prefers_cli(monkeypatch):
    monkeypatch.setattr(demo_live_fleet_reset.settings, "DEV_FLEET_ID", 42)

    assert demo_live_fleet_reset.resolve_live_fleet_id(cli_fleet_id=99) == 99


def test_resolve_live_fleet_id_uses_dev_fleet_id(monkeypatch):
    monkeypatch.setattr(demo_live_fleet_reset.settings, "DEV_FLEET_ID", 42)

    assert demo_live_fleet_reset.resolve_live_fleet_id() == 42


def _insert_live_fleet_rows(db, label: str, suffix: int) -> int:
    fleet = Fleet(name=f"{label.title()} Fleet")
    db.add(fleet)
    db.flush()

    truck = Truck(
        truck_id=f"{label.upper()}-TRUCK-{suffix}",
        fleet_id=fleet.id,
        status="active",
        current_location="Austin, TX",
        current_lat=30.2672,
        current_lon=-97.7431,
        last_seen_at=BASE_DATE,
    )
    driver = Driver(
        driver_id=f"{label.upper()}-DRIVER-{suffix}",
        fleet_id=fleet.id,
        name=f"{label.title()} Driver",
        status="available",
    )
    db.add_all([truck, driver])
    db.flush()

    load = Load(
        load_id=f"{label.upper()}-LOAD-{suffix}",
        fleet_id=fleet.id,
        truck_id=truck.truck_id,
        driver_id=driver.driver_id,
        status="booked",
    )
    db.add(load)
    db.flush()

    db.add_all(
        [
            DwellEvent(
                load_id=load.load_id,
                fleet_id=fleet.id,
                facility_name="Austin Yard",
            ),
            TelemetryEvent(
                truck_id=truck.truck_id,
                fleet_id=fleet.id,
                timestamp=BASE_DATE,
                gps_lat=30.2672,
                gps_lon=-97.7431,
                speed=55,
            ),
            Alert(
                truck_id=truck.truck_id,
                fleet_id=fleet.id,
                severity="high",
                alert_type="late",
                message="Late pickup",
            ),
            User(
                firebase_uid=f"{label}-user",
                email=f"{label}@fleetos.local",
                name=f"{label.title()} User",
                fleet_id=fleet.id,
                role="admin",
            ),
        ]
    )
    db.commit()

    return fleet.id


def _counts_for_fleet(db, fleet_id: int) -> dict[str, int]:
    return {
        "alerts": db.query(Alert).filter(Alert.fleet_id == fleet_id).count(),
        "telemetry_events": db.query(TelemetryEvent)
        .filter(TelemetryEvent.fleet_id == fleet_id)
        .count(),
        "dwell_events": db.query(DwellEvent)
        .filter(DwellEvent.fleet_id == fleet_id)
        .count(),
        "loads": db.query(Load).filter(Load.fleet_id == fleet_id).count(),
        "drivers": db.query(Driver).filter(Driver.fleet_id == fleet_id).count(),
        "trucks": db.query(Truck).filter(Truck.fleet_id == fleet_id).count(),
    }
