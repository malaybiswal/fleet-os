import logging

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base
from app.jobs import simulator_telemetry_ingestion
from app.models.fleet import Fleet
from app.seed.mock_fleets import DEMO_FLEET_NAMES


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


def test_ingest_simulated_telemetry_maps_and_ingests_payloads(monkeypatch):
    payloads = [
        {
            "vehicle_id": "SIM-001",
            "fleet_id": 17,
            "timestamp": "2026-01-01T12:00:00+00:00",
            "location": {
                "description": "Austin, TX",
                "lat": 30.2672,
                "lon": -97.7431,
            },
            "speed_mph": 55.5,
            "status": "active",
        },
        {
            "vehicle_id": "SIM-002",
            "fleet_id": 17,
            "timestamp": "2026-01-01T12:01:00+00:00",
            "location": {
                "description": "Dallas, TX",
                "lat": 32.7767,
                "lon": -96.7970,
            },
            "speed_mph": 45.0,
            "status": "idle",
        },
    ]

    ingested_events = []

    class FakeSession:
        def close(self):
            pass

    class FakeTelemetryIngestionService:
        def __init__(self, db, auto_create_trucks=False):
            self.db = db
            self.auto_create_trucks = auto_create_trucks
            assert auto_create_trucks is True

        def ingest(self, event):
            ingested_events.append(event)

    monkeypatch.setattr(
        simulator_telemetry_ingestion,
        "SessionLocal",
        lambda: FakeSession(),
    )
    monkeypatch.setattr(
        simulator_telemetry_ingestion,
        "TelemetryIngestionService",
        FakeTelemetryIngestionService,
    )
    monkeypatch.setattr(
        simulator_telemetry_ingestion,
        "fetch_simulated_vehicle_payloads",
        lambda fleet_id: payloads,
    )

    def fake_resolve_fleet_id(cli_fleet_id=None, db=None):
        assert cli_fleet_id is None
        assert db is not None
        return 42

    monkeypatch.setattr(
        simulator_telemetry_ingestion,
        "resolve_simulator_fleet_id",
        fake_resolve_fleet_id,
    )

    count = simulator_telemetry_ingestion.ingest_simulated_telemetry()

    assert count == 2
    assert len(ingested_events) == 2
    assert ingested_events[0].truck_id == "SIM-001"
    assert ingested_events[0].fleet_id == 42
    assert ingested_events[0].source == "simulator"
    assert ingested_events[1].truck_id == "SIM-002"
    assert ingested_events[1].fleet_id == 42


def test_ingest_simulated_telemetry_prefers_cli_fleet_id(monkeypatch):
    payloads = [
        {
            "vehicle_id": "SIM-001",
            "fleet_id": 17,
            "timestamp": "2026-01-01T12:00:00+00:00",
            "location": {
                "description": "Austin, TX",
                "lat": 30.2672,
                "lon": -97.7431,
            },
            "speed_mph": 55.5,
            "status": "active",
        },
    ]
    ingested_events = []

    class FakeSession:
        def close(self):
            pass

    class FakeTelemetryIngestionService:
        def __init__(self, db, auto_create_trucks=False):
            pass

        def ingest(self, event):
            ingested_events.append(event)

    monkeypatch.setattr(
        simulator_telemetry_ingestion,
        "SessionLocal",
        lambda: FakeSession(),
    )
    monkeypatch.setattr(
        simulator_telemetry_ingestion,
        "TelemetryIngestionService",
        FakeTelemetryIngestionService,
    )
    monkeypatch.setattr(
        simulator_telemetry_ingestion,
        "fetch_simulated_vehicle_payloads",
        lambda fleet_id: payloads,
    )

    count = simulator_telemetry_ingestion.ingest_simulated_telemetry(fleet_id=99)

    assert count == 1
    assert ingested_events[0].fleet_id == 99


def test_resolve_simulator_fleet_id_prefers_cli(db):
    assert simulator_telemetry_ingestion.resolve_simulator_fleet_id(
        cli_fleet_id=99,
        db=db,
    ) == 99


def test_resolve_simulator_fleet_id_finds_existing_demo_fleet(db):
    fleet = Fleet(name=DEMO_FLEET_NAMES[1])
    db.add(fleet)
    db.commit()
    db.refresh(fleet)

    assert simulator_telemetry_ingestion.resolve_simulator_fleet_id(db=db) == fleet.id
    assert db.query(Fleet).count() == 1


def test_resolve_simulator_fleet_id_creates_demo_fleet(db):
    fleet_id = simulator_telemetry_ingestion.resolve_simulator_fleet_id(db=db)

    fleet = db.query(Fleet).filter(Fleet.id == fleet_id).one()
    assert fleet.name == DEMO_FLEET_NAMES[0]


def test_resolve_simulator_fleet_id_raises_clear_error_when_db_unavailable():
    class FailingSession:
        def query(self, model):
            raise SQLAlchemyError("database unavailable")

        def rollback(self):
            pass

    with pytest.raises(
        simulator_telemetry_ingestion.SimulatorFleetResolutionError,
        match="supply --fleet-id explicitly",
    ):
        simulator_telemetry_ingestion.resolve_simulator_fleet_id(
            db=FailingSession(),
        )


def test_poll_simulated_telemetry_repeats_and_sleeps(monkeypatch):
    calls = []
    sleeps = []

    def fake_ingest(fleet_id=None):
        calls.append(fleet_id)
        return 5

    monkeypatch.setattr(
        simulator_telemetry_ingestion,
        "ingest_simulated_telemetry",
        fake_ingest,
    )

    simulator_telemetry_ingestion.poll_simulated_telemetry(
        fleet_id=17,
        interval_seconds=5,
        sleep_fn=sleeps.append,
        max_iterations=2,
    )

    assert calls == [17, 17]
    assert sleeps == [5]


def test_poll_simulated_telemetry_logs_failure_and_continues(monkeypatch, caplog):
    calls = []

    def fake_ingest(fleet_id=None):
        calls.append(fleet_id)
        if len(calls) == 1:
            raise RuntimeError("temporary outage")
        return 5

    monkeypatch.setattr(
        simulator_telemetry_ingestion,
        "ingest_simulated_telemetry",
        fake_ingest,
    )

    with caplog.at_level(logging.ERROR):
        simulator_telemetry_ingestion.poll_simulated_telemetry(
            fleet_id=17,
            interval_seconds=5,
            sleep_fn=lambda seconds: None,
            max_iterations=2,
        )

    assert calls == [17, 17]
    assert "Simulator poll failed" in caplog.text
