from datetime import datetime, timezone
from decimal import Decimal

from app.database import SessionLocal
from app.models.alert import Alert
from app.models.dwell_event import DwellEvent
from app.models.driver import Driver
from app.models.load import Load
from app.models.truck import Truck
from app.services.dashboard_service import DashboardService

TEST_TRUCK_ID = "TEST-DASH-TRUCK-001"
TEST_DRIVER_ID = "TEST-DASH-DRIVER-001"
TEST_LOAD_ID = "TEST-DASH-LOAD-001"


def _cleanup(db):
    db.query(Alert).filter(Alert.truck_id == TEST_TRUCK_ID).delete()
    db.query(DwellEvent).filter(DwellEvent.load_id == TEST_LOAD_ID).delete()
    db.query(Load).filter(Load.load_id == TEST_LOAD_ID).delete()
    db.query(Driver).filter(Driver.driver_id == TEST_DRIVER_ID).delete()
    db.query(Truck).filter(Truck.truck_id == TEST_TRUCK_ID).delete()
    db.commit()


def test_dashboard_summary_calculates_kpis():
    db = SessionLocal()
    service = DashboardService()

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
            status="on_load",
        )
        load = Load(
            load_id=TEST_LOAD_ID,
            truck_id=TEST_TRUCK_ID,
            driver_id=TEST_DRIVER_ID,
            broker_name="Test Broker",
            origin="Austin, TX",
            destination="Dallas, TX",
            revenue=Decimal("1000.00"),
            miles=Decimal("500.00"),
            deadhead_miles=Decimal("50.00"),
            fuel_cost=Decimal("250.00"),
            maintenance_reserve=Decimal("100.00"),
            driver_cost=Decimal("300.00"),
            tolls=Decimal("25.00"),
            pickup_time=datetime(2026, 5, 10, 8, 0, tzinfo=timezone.utc),
            delivery_time=datetime(2026, 5, 10, 18, 0, tzinfo=timezone.utc),
            status="delivered",
        )
        dwell = DwellEvent(
            load_id=TEST_LOAD_ID,
            facility_name="Test Facility",
            broker_name="Test Broker",
            appointment_time=datetime(2026, 5, 10, 8, 0, tzinfo=timezone.utc),
            arrival_time=datetime(2026, 5, 10, 8, 0, tzinfo=timezone.utc),
            loading_start=datetime(2026, 5, 10, 9, 0, tzinfo=timezone.utc),
            loading_end=datetime(2026, 5, 10, 11, 0, tzinfo=timezone.utc),
            departure_time=datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc),
            detention_pay=Decimal("100.00"),
        )
        alert = Alert(
            truck_id=TEST_TRUCK_ID,
            severity="medium",
            alert_type="low_fuel",
            message="Test alert",
            resolved=False,
        )

        db.add(truck)
        db.add(driver)
        db.commit()

        db.add(load)
        db.commit()

        db.add(dwell)
        db.add(alert)
        db.commit()

        summary = service.get_summary(db=db)

        assert summary["active_trucks"] >= 1
        assert summary["open_alerts"] >= 1
        assert summary["total_revenue"] >= Decimal("1000.00")
        assert summary["avg_revenue_per_mile"] >= Decimal("2.00")
        assert summary["deadhead_percentage"] >= 10.0
        assert summary["fuel_cost_per_mile"] >= Decimal("0.50")
        assert summary["avg_dwell_hours"] >= 4.0

    finally:
        _cleanup(db)
        db.close()