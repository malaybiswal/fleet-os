from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.alert import Alert
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.dependencies.fleet import get_current_fleet_id
from app.models.fleet import Fleet

client = TestClient(app)

TEST_TRUCK_ID = "TEST-API-TRUCK-001"
TEST_FLEET_ID = 999998
TEST_FLEET_NAME = "Telemetry Test Fleet"


def _cleanup():
    db = SessionLocal()
    try:
        db.query(Alert).filter(Alert.truck_id == TEST_TRUCK_ID).delete()
        db.query(TelemetryEvent).filter(TelemetryEvent.truck_id == TEST_TRUCK_ID).delete()
        db.query(Truck).filter(Truck.truck_id == TEST_TRUCK_ID).delete()
        db.query(Fleet).filter(Fleet.id == TEST_FLEET_ID).delete()
        db.commit()
    finally:
        db.close()


def _create_truck():
    db = SessionLocal()
    try:
        fleet = Fleet(
            id=TEST_FLEET_ID,
            name=TEST_FLEET_NAME,
        )
        db.merge(fleet)
        db.commit()
        truck = Truck(
            truck_id=TEST_TRUCK_ID,
            status="active",
            current_location="Austin, TX",
            fleet_id=TEST_FLEET_ID,
        )
        db.add(truck)
        db.commit()
    finally:
        db.close()


def test_get_trucks_returns_list():
    response = client.get("/api/trucks")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_post_telemetry_ingests_event_and_updates_truck():
    _cleanup()
    _create_truck()

    app.dependency_overrides[get_current_fleet_id] = lambda: TEST_FLEET_ID

    try:
        payload = {
            "truck_id": TEST_TRUCK_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "speed": "55.00",
            "fuel_level": "65.00",
            "engine_temp": "190.00",
            "gps_lat": "30.267200",
            "gps_lon": "-97.743100",
            "reefer_temp": "36.00",
        }

        response = client.post("/api/telemetry", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["truck_id"] == TEST_TRUCK_ID

        telemetry_response = client.get(f"/api/telemetry/{TEST_TRUCK_ID}")
        assert telemetry_response.status_code == 200
        assert len(telemetry_response.json()) >= 1

    finally:
        app.dependency_overrides.clear()
        _cleanup()


def test_get_telemetry_unknown_truck_returns_404():
    response = client.get("/api/telemetry/DOES-NOT-EXIST")

    assert response.status_code == 404
    assert "error" in response.json()