from decimal import Decimal

from app.database import SessionLocal
from app.models.driver import Driver
from app.models.load import Load
from app.models.truck import Truck
from app.services.load_service import LoadService

TEST_TRUCK_ID = "TEST-LOAD-TRUCK-001"
TEST_DRIVER_ID = "TEST-LOAD-DRIVER-001"
TEST_LOAD_ID = "TEST-LOAD-001"


def _cleanup(db):
    db.query(Load).filter(Load.load_id == TEST_LOAD_ID).delete()
    db.query(Driver).filter(Driver.driver_id == TEST_DRIVER_ID).delete()
    db.query(Truck).filter(Truck.truck_id == TEST_TRUCK_ID).delete()
    db.commit()


def test_load_service_calculates_profitability():
    db = SessionLocal()
    service = LoadService()

    try:
        _cleanup(db)

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

        load = Load(
            load_id=TEST_LOAD_ID,
            truck_id=TEST_TRUCK_ID,
            driver_id=TEST_DRIVER_ID,
            broker_name="Test Broker",
            origin="Austin, TX",
            destination="Dallas, TX",
            revenue=Decimal("2500.00"),
            miles=Decimal("210.00"),
            deadhead_miles=Decimal("25.00"),
            fuel_cost=Decimal("450.00"),
            maintenance_reserve=Decimal("100.00"),
            driver_cost=Decimal("700.00"),
            tolls=Decimal("50.00"),
            status="booked",
        )

        db.add(load)
        db.commit()

        result = service.get_profitability(db, TEST_LOAD_ID)

        assert result is not None
        assert result.load_id == TEST_LOAD_ID
        assert result.revenue == Decimal("2500.00")
        assert result.miles == Decimal("210.00")
        assert result.deadhead_miles == Decimal("25.00")
        assert result.revenue_per_mile == Decimal("11.90")
        assert result.deadhead_percentage == Decimal("11.90")
        assert result.net_profit == Decimal("1200.00")

    finally:
        _cleanup(db)
        db.close()


def test_load_service_returns_none_for_missing_load():
    db = SessionLocal()
    service = LoadService()

    try:
        result = service.get_profitability(db, "MISSING-LOAD-ID")

        assert result is None
    finally:
        db.close()