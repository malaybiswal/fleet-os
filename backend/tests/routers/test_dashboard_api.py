from fastapi.testclient import TestClient
from app.database import SessionLocal
from app.dependencies.fleet import get_current_fleet_id
from app.models.fleet import Fleet
from app.models.truck import Truck
from app.main import app

client = TestClient(app)

TEST_FLEET_1_ID = 999998
TEST_FLEET_2_ID = 999999
TEST_FLEET_1_NAME = "Dashboard Test Fleet 999998"
TEST_FLEET_2_NAME = "Dashboard Test Fleet 999999"
TEST_TRUCK_ID = "TEST-DASHBOARD-TRUCK-001"
TEST_OTHER_TRUCK_ID = "TEST-DASHBOARD-TRUCK-002"


def _cleanup():
    db = SessionLocal()
    try:
        db.query(Truck).filter(
            Truck.truck_id.in_([TEST_TRUCK_ID, TEST_OTHER_TRUCK_ID])
        ).delete(synchronize_session=False)

        db.query(Fleet).filter(
            Fleet.id.in_([TEST_FLEET_1_ID, TEST_FLEET_2_ID])
        ).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()

def test_dashboard_summary_scopes_active_trucks_to_current_fleet():
    _cleanup()
    app.dependency_overrides[get_current_fleet_id] = lambda: TEST_FLEET_1_ID

    db = SessionLocal()
    try:
        db.add_all(
            [
                Fleet(id=TEST_FLEET_1_ID, name=TEST_FLEET_1_NAME),
                Fleet(id=TEST_FLEET_2_ID, name=TEST_FLEET_2_NAME),
                Truck(
                    truck_id=TEST_TRUCK_ID,
                    status="moving",
                    current_location="Austin, TX",
                    fleet_id=TEST_FLEET_1_ID,
                ),
                Truck(
                    truck_id=TEST_OTHER_TRUCK_ID,
                    status="active",
                    current_location="Dallas, TX",
                    fleet_id=TEST_FLEET_2_ID,
                ),
            ]
        )
        db.commit()

        response = client.get("/api/dashboard/summary")

        assert response.status_code == 200
        body = response.json()
        assert body["active_trucks"] == 1

    finally:
        app.dependency_overrides.clear()
        _cleanup()

def test_dashboard_summary_endpoint_returns_expected_shape():
    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()

    assert "active_trucks" in body
    assert "avg_dwell_hours" in body
    assert "total_revenue" in body
    assert "avg_revenue_per_mile" in body
    assert "deadhead_percentage" in body
    assert "open_alerts" in body
    assert "open_loads" in body
    assert "fuel_cost_per_mile" in body


def test_dashboard_summary_accepts_date_filters():
    response = client.get(
        "/api/dashboard/summary",
        params={
            "start_date": "2026-05-01T00:00:00Z",
            "end_date": "2026-05-31T23:59:59Z",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert "active_trucks" in body
    assert "open_alerts" in body
