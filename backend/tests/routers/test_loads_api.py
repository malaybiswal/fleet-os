from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.driver import Driver
from app.models.dwell_event import DwellEvent
from app.models.facility import Facility, normalize_facility_name
from app.models.load import Load
from app.models.truck import Truck
from app.models.fleet import Fleet
from app.dependencies.fleet import get_current_fleet_id

client = TestClient(app)

TEST_TRUCK_ID = "TEST-API-LOAD-TRUCK-001"
TEST_DRIVER_ID = "TEST-API-LOAD-DRIVER-001"
TEST_LOAD_ID = "TEST-API-LOAD-001"
TEST_OTHER_TRUCK_ID = "TEST-API-LOAD-TRUCK-002"
TEST_OTHER_DRIVER_ID = "TEST-API-LOAD-DRIVER-002"
TEST_OTHER_LOAD_ID = "TEST-API-LOAD-002"

TEST_FLEET_1_ID = 999998
TEST_FLEET_2_ID = 999999

TEST_FLEET_1_NAME = "Test Fleet 999998"
TEST_FLEET_2_NAME = "Test Fleet 999999"

TEST_FACILITY_NAME = "Test API Risk Facility"


def _cleanup():
    db = SessionLocal()
    try:
        db.query(DwellEvent).filter(
            DwellEvent.load_id.in_([TEST_LOAD_ID, TEST_OTHER_LOAD_ID])
        ).delete(synchronize_session=False)

        db.query(Load).filter(
            Load.load_id.in_([TEST_LOAD_ID, TEST_OTHER_LOAD_ID])
        ).delete(synchronize_session=False)

        db.query(Truck).filter(
            Truck.truck_id.in_([TEST_TRUCK_ID, TEST_OTHER_TRUCK_ID])
        ).delete(synchronize_session=False)

        db.query(Driver).filter(
            Driver.driver_id.in_([TEST_DRIVER_ID, TEST_OTHER_DRIVER_ID])
        ).delete(synchronize_session=False)

        db.query(Facility).filter(
            Facility.fleet_id.in_([TEST_FLEET_1_ID, TEST_FLEET_2_ID])
        ).delete(synchronize_session=False)

        db.query(Fleet).filter(
            Fleet.id.in_([TEST_FLEET_1_ID, TEST_FLEET_2_ID])
        ).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()


def _seed_truck_and_driver():
    db = SessionLocal()
    try:
        fleet = (
            db.query(Fleet)
            .filter(Fleet.id == TEST_FLEET_1_ID)
            .first()
        )

        if fleet is None:
            fleet = Fleet(
                id=TEST_FLEET_1_ID,
                name=TEST_FLEET_1_NAME,
            )
            db.add(fleet)
            db.commit()
            db.refresh(fleet)

        truck = Truck(
            truck_id=TEST_TRUCK_ID,
            status="active",
            current_location="Austin, TX",
            fleet_id=fleet.id,
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


def test_get_loads_endpoint_returns_only_current_fleet_loads():
    _cleanup()
    app.dependency_overrides[get_current_fleet_id] = lambda: TEST_FLEET_1_ID

    db = SessionLocal()
    try:
        fleet_1 = Fleet(id=TEST_FLEET_1_ID, name=TEST_FLEET_1_NAME)
        fleet_2 = Fleet(id=TEST_FLEET_2_ID, name=TEST_FLEET_2_NAME)
        db.merge(fleet_1)
        db.merge(fleet_2)
        db.commit()

        truck_1 = Truck(
            truck_id=TEST_TRUCK_ID,
            status="active",
            current_location="Austin, TX",
            fleet_id=TEST_FLEET_1_ID,
        )
        truck_2 = Truck(
            truck_id=TEST_OTHER_TRUCK_ID,
            status="active",
            current_location="Dallas, TX",
            fleet_id=TEST_FLEET_2_ID,
        )
        driver_1 = Driver(
            driver_id=TEST_DRIVER_ID,
            name="Test Driver 1",
            status="available",
        )
        driver_2 = Driver(
            driver_id=TEST_OTHER_DRIVER_ID,
            name="Test Driver 2",
            status="available",
        )
        load_1 = Load(
            load_id=TEST_LOAD_ID,
            truck_id=TEST_TRUCK_ID,
            driver_id=TEST_DRIVER_ID,
            broker_name="Broker One",
            origin="Austin, TX",
            destination="Dallas, TX",
            revenue=2500,
            miles=210,
            deadhead_miles=25,
            fuel_cost=450,
            maintenance_reserve=100,
            driver_cost=700,
            tolls=50,
            status="booked",
            fleet_id=TEST_FLEET_1_ID,
        )
        load_2 = Load(
            load_id=TEST_OTHER_LOAD_ID,
            truck_id=TEST_OTHER_TRUCK_ID,
            driver_id=TEST_OTHER_DRIVER_ID,
            broker_name="Broker Two",
            origin="Houston, TX",
            destination="Laredo, TX",
            revenue=3000,
            miles=330,
            deadhead_miles=40,
            fuel_cost=650,
            maintenance_reserve=120,
            driver_cost=900,
            tolls=75,
            status="booked",
            fleet_id=TEST_FLEET_2_ID,
        )

        db.add_all([truck_1, truck_2, driver_1, driver_2, load_1, load_2])
        db.commit()

        response = client.get("/api/loads")

        assert response.status_code == 200
        load_ids = {load["load_id"] for load in response.json()}

        assert TEST_LOAD_ID in load_ids
        assert TEST_OTHER_LOAD_ID not in load_ids

    finally:
        app.dependency_overrides.clear()
        _cleanup()


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


def test_get_loads_endpoint_includes_facility_risk():
    _cleanup()
    app.dependency_overrides[get_current_fleet_id] = lambda: TEST_FLEET_1_ID

    db = SessionLocal()
    try:
        fleet = Fleet(id=TEST_FLEET_1_ID, name=TEST_FLEET_1_NAME)
        db.merge(fleet)
        db.commit()

        facility = Facility(
            fleet_id=TEST_FLEET_1_ID,
            name=TEST_FACILITY_NAME,
            normalized_name=normalize_facility_name(TEST_FACILITY_NAME),
        )
        db.add(facility)
        db.commit()
        db.refresh(facility)

        truck_1 = Truck(
            truck_id=TEST_TRUCK_ID,
            status="active",
            current_location="Austin, TX",
            fleet_id=TEST_FLEET_1_ID,
        )
        truck_2 = Truck(
            truck_id=TEST_OTHER_TRUCK_ID,
            status="active",
            current_location="Dallas, TX",
            fleet_id=TEST_FLEET_1_ID,
        )
        driver_1 = Driver(
            driver_id=TEST_DRIVER_ID,
            name="Test Driver 1",
            status="available",
        )
        driver_2 = Driver(
            driver_id=TEST_OTHER_DRIVER_ID,
            name="Test Driver 2",
            status="available",
        )
        load_1 = Load(
            load_id=TEST_LOAD_ID,
            truck_id=TEST_TRUCK_ID,
            driver_id=TEST_DRIVER_ID,
            broker_name="Broker One",
            origin="Austin, TX",
            destination="Dallas, TX",
            revenue=2500,
            miles=210,
            deadhead_miles=25,
            fuel_cost=450,
            maintenance_reserve=100,
            driver_cost=700,
            tolls=50,
            status="booked",
            fleet_id=TEST_FLEET_1_ID,
        )
        load_2 = Load(
            load_id=TEST_OTHER_LOAD_ID,
            truck_id=TEST_OTHER_TRUCK_ID,
            driver_id=TEST_OTHER_DRIVER_ID,
            broker_name="Broker Two",
            origin="Houston, TX",
            destination="Laredo, TX",
            revenue=3000,
            miles=330,
            deadhead_miles=40,
            fuel_cost=650,
            maintenance_reserve=120,
            driver_cost=900,
            tolls=75,
            status="booked",
            fleet_id=TEST_FLEET_1_ID,
        )

        db.add_all([truck_1, truck_2, driver_1, driver_2, load_1, load_2])
        db.commit()

        arrival = datetime.now(timezone.utc) - timedelta(days=1)
        db.add(
            DwellEvent(
                load_id=TEST_LOAD_ID,
                fleet_id=TEST_FLEET_1_ID,
                facility_id=facility.id,
                facility_name=facility.name,
                arrival_time=arrival,
                departure_time=arrival + timedelta(hours=8),
                detention_pay=450,
            )
        )
        db.commit()

        response = client.get("/api/loads")

        assert response.status_code == 200
        loads_by_id = {load["load_id"]: load for load in response.json()}

        risky_load = loads_by_id[TEST_LOAD_ID]
        assert risky_load["facility_risk"] is not None
        assert risky_load["facility_risk"]["facility_name"] == TEST_FACILITY_NAME
        assert risky_load["facility_risk"]["detention_risk_band"] == "high"
        assert risky_load["facility_risk"]["visit_count"] == 1

        load_without_visits = loads_by_id[TEST_OTHER_LOAD_ID]
        assert load_without_visits["facility_risk"] is None

    finally:
        app.dependency_overrides.clear()
        _cleanup()