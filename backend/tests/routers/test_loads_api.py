from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.driver import Driver
from app.models.load import Load
from app.models.truck import Truck

client = TestClient(app)

TEST_TRUCK_ID = "TEST-API-LOAD-TRUCK-001"
TEST_DRIVER_ID = "TEST-API-LOAD-DRIVER-001"
TEST_LOAD_ID = "TEST-API-LOAD-001"


def _cleanup():
    db = SessionLocal()
    try:
        db.query(Load).filter(Load.load_id == TEST_LOAD_ID).delete()
        db.query(Driver).filter(Driver.driver_id == TEST_DRIVER_ID).delete()
        db.query(Truck).filter(Truck.truck_id == TEST_TRUCK_ID).delete()
        db.commit()
    finally:
        db.close()


def _seed_truck_and_driver():
    db = SessionLocal()
    try:
        truck = Truck(
            truck_id=TEST_TRUCK_ID,
            status="active",
            current_location="Austin, TX",
        )
        driver = Driver(
            driver_id=TEST_DRIVER_ID,
            name="Test Driver",
            status="available",
        )

        db.add(truck)
        db.add(driver)
        db.commit()
    finally:
        db.close()


def test_get_loads_endpoint_returns_list():
    response = client.get("/api/loads")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_load_and_get_profitability():
    _cleanup()
    _seed_truck_and_driver()

    try:
        create_response = client.post(
            "/api/loads",
            json={
                "load_id": TEST_LOAD_ID,
                "truck_id": TEST_TRUCK_ID,
                "driver_id": TEST_DRIVER_ID,
                "broker_name": "Test Broker",
                "origin": "Austin, TX",
                "destination": "Dallas, TX",
                "revenue": 2500,
                "miles": 210,
                "deadhead_miles": 25,
                "fuel_cost": 450,
                "maintenance_reserve": 100,
                "driver_cost": 700,
                "tolls": 50,
                "status": "booked",
            },
        )

        assert create_response.status_code == 200
        created = create_response.json()
        assert created["load_id"] == TEST_LOAD_ID

        profit_response = client.get(f"/api/loads/{TEST_LOAD_ID}/profitability")

        assert profit_response.status_code == 200
        body = profit_response.json()

        assert body["load_id"] == TEST_LOAD_ID
        assert body["revenue"] == "2500.00"
        assert body["miles"] == "210.00"
        assert body["deadhead_miles"] == "25.00"
        assert body["revenue_per_mile"] == "11.90"
        assert body["deadhead_percentage"] == "11.90"
        assert body["net_profit"] == "1200.00"

    finally:
        _cleanup()


def test_load_profitability_returns_404_for_missing_load():
    response = client.get("/api/loads/MISSING-LOAD-ID/profitability")

    assert response.status_code == 404
    assert response.json()["error"] == "Load MISSING-LOAD-ID not found"