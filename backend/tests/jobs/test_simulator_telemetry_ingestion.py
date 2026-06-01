import logging

from app.jobs import simulator_telemetry_ingestion


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
        lambda: payloads,
    )
    monkeypatch.setattr(simulator_telemetry_ingestion.settings, "DEV_FLEET_ID", 42)

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
        lambda: payloads,
    )
    monkeypatch.setattr(simulator_telemetry_ingestion.settings, "DEV_FLEET_ID", 42)

    count = simulator_telemetry_ingestion.ingest_simulated_telemetry(fleet_id=99)

    assert count == 1
    assert ingested_events[0].fleet_id == 99


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
