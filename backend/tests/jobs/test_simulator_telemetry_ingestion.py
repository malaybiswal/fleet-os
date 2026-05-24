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

    count = simulator_telemetry_ingestion.ingest_simulated_telemetry()

    assert count == 2
    assert len(ingested_events) == 2
    assert ingested_events[0].truck_id == "SIM-001"
    assert ingested_events[0].fleet_id == 17
    assert ingested_events[0].source == "simulator"
    assert ingested_events[1].truck_id == "SIM-002"
