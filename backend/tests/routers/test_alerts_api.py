from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.alert import Alert
from app.models.truck import Truck

from app.dependencies.fleet import get_current_fleet_id
from app.models.fleet import Fleet

client = TestClient(app)

TEST_TRUCK_ID = "TEST-ALERT-API-TRUCK-001"
TEST_FLEET_ID = 999998
TEST_FLEET_NAME = "Alert API Test Fleet"


def _cleanup():
    db = SessionLocal()
    try:
        db.query(Alert).filter(Alert.truck_id == TEST_TRUCK_ID).delete()
        db.query(Truck).filter(Truck.truck_id == TEST_TRUCK_ID).delete()
        db.query(Fleet).filter(Fleet.id == TEST_FLEET_ID).delete()
        db.commit()
    finally:
        db.close()


def _create_truck():
    db = SessionLocal()
    try:
        fleet = Fleet(id=TEST_FLEET_ID, name=TEST_FLEET_NAME)
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


def _create_alert(resolved: bool = False) -> int:
    db = SessionLocal()
    try:
        alert = Alert(
            truck_id=TEST_TRUCK_ID,
            severity="medium",
            alert_type="low_fuel",
            message="Fuel level at 12% for truck TEST-ALERT-API-TRUCK-001",
            resolved=resolved,
            fleet_id=TEST_FLEET_ID,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert.id
    finally:
        db.close()


def test_get_alerts_returns_list():
    response = client.get("/api/alerts")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_alerts_filter_unresolved():
    _cleanup()
    app.dependency_overrides[get_current_fleet_id] = lambda: TEST_FLEET_ID

    try:
        _create_truck()
        _create_alert(resolved=False)
        _create_alert(resolved=True)

        response = client.get("/api/alerts?resolved=false")

        assert response.status_code == 200
        body = response.json()
        assert len(body) >= 1
        assert all(
            alert["resolved"] is False
            for alert in body
            if alert["truck_id"] == TEST_TRUCK_ID
        )

    finally:
        app.dependency_overrides.clear()
        _cleanup()


def test_resolve_alert():
    _cleanup()
    app.dependency_overrides[get_current_fleet_id] = lambda: TEST_FLEET_ID
    try:
        _create_truck()
        alert_id = _create_alert(resolved=False)

        response = client.patch(f"/api/alerts/{alert_id}/resolve")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == alert_id
        assert body["resolved"] is True

    finally:
        app.dependency_overrides.clear()
        _cleanup()


def test_resolve_missing_alert_returns_404():
    app.dependency_overrides[get_current_fleet_id] = lambda: TEST_FLEET_ID

    try:
        response = client.patch("/api/alerts/999999999/resolve")

        assert response.status_code == 404
        assert "error" in response.json()

    finally:
        app.dependency_overrides.clear()