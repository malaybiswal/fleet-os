from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.ingestion.normalized_events import NormalizedTelemetryEvent
from app.ingestion.telemetry_ingestion_service import (
    TelemetryIngestionService,
    UnknownTruckError,
)
from app.models.fleet import Fleet
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.services.operational_status import OperationalStatus


TEST_DATABASE_URL = "sqlite:///./test_telemetry_ingestion.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_ingest_creates_telemetry_event(db):
    fleet = Fleet(name="Test Fleet")
    db.add(fleet)
    db.commit()
    db.refresh(fleet)

    truck = Truck(
        truck_id="TRUCK-001",
        status="idle",
        fleet_id=fleet.id,
    )

    db.add(truck)
    db.commit()

    service = TelemetryIngestionService(db)

    event = NormalizedTelemetryEvent(
        fleet_id=fleet.id,
        truck_id="TRUCK-001",
        timestamp=datetime.now(timezone.utc),
        latitude=30.506,
        longitude=-97.8305,
        speed_mph=65,
        location_description="Cedar Park, TX",
        status="active",
        source="simulator",
    )

    telemetry_event = service.ingest(event)

    assert isinstance(telemetry_event, TelemetryEvent)
    assert telemetry_event.truck_id == "TRUCK-001"
    assert float(telemetry_event.gps_lat) == 30.506
    assert float(telemetry_event.gps_lon) == -97.8305


def test_ingest_updates_truck_location(db):
    fleet = Fleet(name="Test Fleet")
    db.add(fleet)
    db.commit()
    db.refresh(fleet)

    truck = Truck(
        truck_id="TRUCK-002",
        status="idle",
        fleet_id=fleet.id,
    )

    db.add(truck)
    db.commit()

    service = TelemetryIngestionService(db)

    event = NormalizedTelemetryEvent(
        fleet_id=fleet.id,
        truck_id="TRUCK-002",
        timestamp=datetime.now(timezone.utc),
        latitude=31.0,
        longitude=-98.0,
        speed_mph=10,
        location_description="Austin, TX",
        status="active",
        source="simulator",
    )

    service.ingest(event)

    updated_truck = (
        db.query(Truck)
        .filter(Truck.truck_id == "TRUCK-002")
        .first()
    )

    assert updated_truck is not None
    assert float(updated_truck.current_lat) == 31.0
    assert float(updated_truck.current_lon) == -98.0
    assert updated_truck.current_location == "Austin, TX"
    assert updated_truck.status == OperationalStatus.SLOW.value


@pytest.mark.parametrize(
    ("speed_mph", "reported_status", "expected_status"),
    [
        (55, "active", OperationalStatus.MOVING.value),
        (10, "active", OperationalStatus.SLOW.value),
        (3, "idle", OperationalStatus.IDLE.value),
        (0, "active", OperationalStatus.STOPPED.value),
        (55, "maintenance", OperationalStatus.MAINTENANCE.value),
    ],
)
def test_ingest_derives_operational_status_from_speed(
    db,
    speed_mph,
    reported_status,
    expected_status,
):
    fleet = Fleet(name="Test Fleet")
    db.add(fleet)
    db.commit()
    db.refresh(fleet)

    truck = Truck(
        truck_id="TRUCK-STATUS",
        status="idle",
        fleet_id=fleet.id,
    )

    db.add(truck)
    db.commit()

    service = TelemetryIngestionService(db)

    event = NormalizedTelemetryEvent(
        fleet_id=fleet.id,
        truck_id="TRUCK-STATUS",
        timestamp=datetime.now(timezone.utc),
        latitude=31.0,
        longitude=-98.0,
        speed_mph=speed_mph,
        status=reported_status,
        source="simulator",
    )

    service.ingest(event)

    updated_truck = (
        db.query(Truck)
        .filter(Truck.truck_id == "TRUCK-STATUS")
        .first()
    )

    assert updated_truck is not None
    assert updated_truck.status == expected_status

def test_ingest_rejects_unknown_truck_by_default(db):
    fleet = Fleet(name="Test Fleet")
    db.add(fleet)
    db.commit()
    db.refresh(fleet)

    service = TelemetryIngestionService(db)

    event = NormalizedTelemetryEvent(
        fleet_id=fleet.id,
        truck_id="UNKNOWN-001",
        timestamp=datetime.now(timezone.utc),
        latitude=30.506,
        longitude=-97.8305,
        source="simulator",
    )

    with pytest.raises(UnknownTruckError):
        service.ingest(event)


def test_ingest_auto_creates_unknown_truck_when_enabled(db):
    fleet = Fleet(name="Test Fleet")
    db.add(fleet)
    db.commit()
    db.refresh(fleet)

    service = TelemetryIngestionService(db, auto_create_trucks=True)

    event = NormalizedTelemetryEvent(
        fleet_id=fleet.id,
        truck_id="SIM-NEW-001",
        timestamp=datetime.now(timezone.utc),
        latitude=30.506,
        longitude=-97.8305,
        speed_mph=55,
        location_description="Cedar Park, TX",
        status="active",
        source="simulator",
    )

    telemetry_event = service.ingest(event)

    created_truck = (
        db.query(Truck)
        .filter(
            Truck.fleet_id == fleet.id,
            Truck.truck_id == "SIM-NEW-001",
        )
        .first()
    )

    assert created_truck is not None
    assert created_truck.status == OperationalStatus.MOVING.value
    assert created_truck.current_location == "Cedar Park, TX"
    assert float(created_truck.current_lat) == 30.506
    assert float(created_truck.current_lon) == -97.8305

    assert telemetry_event.truck_id == "SIM-NEW-001"
