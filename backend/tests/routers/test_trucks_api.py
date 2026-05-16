from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.dependencies.fleet import get_current_fleet_id
from app.main import app
from app.models.fleet import Fleet
from app.models.truck import Truck

client = TestClient(app)

TEST_FLEET_1_ID = 999998
TEST_FLEET_2_ID = 999999
TEST_FLEET_1_NAME = "Test Fleet 999998"
TEST_FLEET_2_NAME = "Test Fleet 999999"
TEST_TRUCK_ID = "TEST-API-TRUCK-001"
TEST_OTHER_TRUCK_ID = "TEST-API-TRUCK-002"


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


def test_get_trucks_endpoint_returns_only_current_fleet_trucks():
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
                    status="active",
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

        response = client.get("/api/trucks")

        assert response.status_code == 200
        truck_ids = {truck["truck_id"] for truck in response.json()}

        assert TEST_TRUCK_ID in truck_ids
        assert TEST_OTHER_TRUCK_ID not in truck_ids

    finally:
        app.dependency_overrides.clear()
        _cleanup()