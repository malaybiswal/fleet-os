import logging

from app.jobs import geotab_telemetry_ingestion


def test_ingest_geotab_telemetry_maps_and_ingests_payloads(monkeypatch):
    payloads = [
        {
            "device": {"id": "b123"},
            "dateTime": "2026-05-30T15:45:00Z",
            "latitude": 32.7767,
            "longitude": -96.797,
            "speed": 100,
            "bearing": 182,
        },
        {
            "device": {"id": "b124"},
            "dateTime": "2026-05-30T15:46:00Z",
            "speed": 0,
        },
    ]
    ingested_events = []

    class FakeSession:
        def close(self):
            pass

    class FakeGeotabClient:
        def fetch_device_status_info(self):
            return payloads

        def close(self):
            pass

    class FakeTelemetryIngestionService:
        def __init__(self, db, auto_create_trucks=False):
            self.db = db
            self.auto_create_trucks = auto_create_trucks
            assert auto_create_trucks is True

        def ingest(self, event):
            ingested_events.append(event)

    monkeypatch.setattr(geotab_telemetry_ingestion, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(
        geotab_telemetry_ingestion,
        "build_geotab_client",
        lambda database, username, password: FakeGeotabClient(),
    )
    monkeypatch.setattr(
        geotab_telemetry_ingestion,
        "TelemetryIngestionService",
        FakeTelemetryIngestionService,
    )
    monkeypatch.setattr(geotab_telemetry_ingestion.settings, "GEOTAB_DATABASE", "Demo")
    monkeypatch.setattr(geotab_telemetry_ingestion.settings, "GEOTAB_USERNAME", "user")
    monkeypatch.setattr(geotab_telemetry_ingestion.settings, "GEOTAB_PASSWORD", "pass")

    count = geotab_telemetry_ingestion.ingest_geotab_telemetry(fleet_id=17)

    assert count == 2
    assert len(ingested_events) == 2
    assert ingested_events[0].fleet_id == 17
    assert ingested_events[0].truck_id == "GEOTAB-17-b123"
    assert ingested_events[0].source == "geotab"
    assert ingested_events[1].truck_id == "GEOTAB-17-b124"


def test_ingest_geotab_telemetry_skips_malformed_payloads(monkeypatch, caplog):
    payloads = [
        {"device": {}, "dateTime": "2026-05-30T15:45:00Z"},
        {
            "device": {"id": "b124"},
            "dateTime": "2026-05-30T15:46:00Z",
            "speed": 0,
        },
    ]
    ingested_events = []

    class FakeSession:
        def close(self):
            pass

    class FakeGeotabClient:
        def fetch_device_status_info(self):
            return payloads

        def close(self):
            pass

    class FakeTelemetryIngestionService:
        def __init__(self, db, auto_create_trucks=False):
            pass

        def ingest(self, event):
            ingested_events.append(event)

    monkeypatch.setattr(geotab_telemetry_ingestion, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(
        geotab_telemetry_ingestion,
        "build_geotab_client",
        lambda database, username, password: FakeGeotabClient(),
    )
    monkeypatch.setattr(
        geotab_telemetry_ingestion,
        "TelemetryIngestionService",
        FakeTelemetryIngestionService,
    )
    monkeypatch.setattr(geotab_telemetry_ingestion.settings, "GEOTAB_DATABASE", "Demo")
    monkeypatch.setattr(geotab_telemetry_ingestion.settings, "GEOTAB_USERNAME", "user")
    monkeypatch.setattr(geotab_telemetry_ingestion.settings, "GEOTAB_PASSWORD", "pass")

    count = geotab_telemetry_ingestion.ingest_geotab_telemetry(fleet_id=17)

    assert count == 1
    assert len(ingested_events) == 1
    assert "Skipping malformed Geotab DeviceStatusInfo" in caplog.text


def test_resolve_geotab_fleet_id_prefers_cli():
    assert geotab_telemetry_ingestion.resolve_geotab_fleet_id(cli_fleet_id=17) == 17


def test_resolve_geotab_fleet_id_uses_dev_fleet_id(monkeypatch):
    monkeypatch.setattr(geotab_telemetry_ingestion.settings, "DEV_FLEET_ID", 42)

    assert geotab_telemetry_ingestion.resolve_geotab_fleet_id() == 42


def test_poll_geotab_telemetry_repeats_and_sleeps(monkeypatch):
    calls = []
    sleeps = []

    def fake_ingest(fleet_id=None):
        calls.append(fleet_id)
        return geotab_telemetry_ingestion.GeotabIngestionResult(
            fetched=2,
            ingested=2,
            skipped=0,
        )

    monkeypatch.setattr(
        geotab_telemetry_ingestion,
        "ingest_geotab_telemetry_with_result",
        fake_ingest,
    )

    geotab_telemetry_ingestion.poll_geotab_telemetry(
        fleet_id=17,
        interval_seconds=5,
        sleep_fn=sleeps.append,
        max_iterations=2,
    )

    assert calls == [17, 17]
    assert sleeps == [5]


def test_poll_geotab_telemetry_logs_failure_and_continues(monkeypatch, caplog):
    calls = []

    def fake_ingest(fleet_id=None):
        calls.append(fleet_id)
        if len(calls) == 1:
            raise RuntimeError("temporary outage")
        return geotab_telemetry_ingestion.GeotabIngestionResult(
            fetched=1,
            ingested=1,
            skipped=0,
        )

    monkeypatch.setattr(
        geotab_telemetry_ingestion,
        "ingest_geotab_telemetry_with_result",
        fake_ingest,
    )

    with caplog.at_level(logging.ERROR):
        geotab_telemetry_ingestion.poll_geotab_telemetry(
            fleet_id=17,
            interval_seconds=5,
            sleep_fn=lambda seconds: None,
            max_iterations=2,
        )

    assert calls == [17, 17]
    assert "Geotab poll failed" in caplog.text
