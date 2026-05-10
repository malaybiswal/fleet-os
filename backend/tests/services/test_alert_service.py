from datetime import datetime, timezone
from decimal import Decimal

from app.database import SessionLocal
from app.models.alert import Alert
from app.models.dwell_event import DwellEvent
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.services.alert_service import AlertService


TEST_TRUCK_ID = "TEST-ALERT-TRUCK-001"


def _cleanup(db):
    db.query(Alert).filter(Alert.truck_id == TEST_TRUCK_ID).delete()
    db.query(Truck).filter(Truck.truck_id == TEST_TRUCK_ID).delete()
    db.commit()


def _create_test_truck(db):
    truck = Truck(
        truck_id=TEST_TRUCK_ID,
        status="active",
        current_location="Austin, TX",
    )
    db.add(truck)
    db.commit()
    db.refresh(truck)
    return truck


def test_low_fuel_alert_created():
    db = SessionLocal()
    service = AlertService()

    try:
        _cleanup(db)
        _create_test_truck(db)

        telemetry = TelemetryEvent(
            truck_id=TEST_TRUCK_ID,
            timestamp=datetime.now(timezone.utc),
            fuel_level=Decimal("12.00"),
            engine_temp=Decimal("200.00"),
            reefer_temp=Decimal("36.00"),
        )

        alerts = service.check_telemetry_alerts(db, telemetry)

        assert len(alerts) == 1
        assert alerts[0].alert_type == "low_fuel"
        assert alerts[0].severity == "medium"
        assert "Fuel level" in alerts[0].message

    finally:
        _cleanup(db)
        db.close()


def test_engine_overheat_alert_created():
    db = SessionLocal()
    service = AlertService()

    try:
        _cleanup(db)
        _create_test_truck(db)

        telemetry = TelemetryEvent(
            truck_id=TEST_TRUCK_ID,
            timestamp=datetime.now(timezone.utc),
            fuel_level=Decimal("50.00"),
            engine_temp=Decimal("240.00"),
            reefer_temp=Decimal("36.00"),
        )

        alerts = service.check_telemetry_alerts(db, telemetry)

        assert len(alerts) == 1
        assert alerts[0].alert_type == "engine_overheat"
        assert alerts[0].severity == "high"

    finally:
        _cleanup(db)
        db.close()


def test_reefer_temp_deviation_alert_created():
    db = SessionLocal()
    service = AlertService()

    try:
        _cleanup(db)
        _create_test_truck(db)

        telemetry = TelemetryEvent(
            truck_id=TEST_TRUCK_ID,
            timestamp=datetime.now(timezone.utc),
            fuel_level=Decimal("50.00"),
            engine_temp=Decimal("200.00"),
            reefer_temp=Decimal("42.00"),
        )

        alerts = service.check_telemetry_alerts(db, telemetry)

        assert len(alerts) == 1
        assert alerts[0].alert_type == "reefer_temp_deviation"
        assert alerts[0].severity == "high"

    finally:
        _cleanup(db)
        db.close()


def test_duplicate_unresolved_alert_is_not_created():
    db = SessionLocal()
    service = AlertService()

    try:
        _cleanup(db)
        _create_test_truck(db)

        telemetry = TelemetryEvent(
            truck_id=TEST_TRUCK_ID,
            timestamp=datetime.now(timezone.utc),
            fuel_level=Decimal("12.00"),
            engine_temp=Decimal("200.00"),
            reefer_temp=Decimal("36.00"),
        )

        first = service.check_telemetry_alerts(db, telemetry)
        second = service.check_telemetry_alerts(db, telemetry)

        assert len(first) == 1
        assert len(second) == 0

        count = db.query(Alert).filter(
            Alert.truck_id == TEST_TRUCK_ID,
            Alert.alert_type == "low_fuel",
            Alert.resolved.is_(False),
        ).count()

        assert count == 1

    finally:
        _cleanup(db)
        db.close()


def test_no_alert_when_thresholds_are_normal():
    db = SessionLocal()
    service = AlertService()

    try:
        _cleanup(db)
        _create_test_truck(db)

        telemetry = TelemetryEvent(
            truck_id=TEST_TRUCK_ID,
            timestamp=datetime.now(timezone.utc),
            fuel_level=Decimal("75.00"),
            engine_temp=Decimal("200.00"),
            reefer_temp=Decimal("36.00"),
        )

        alerts = service.check_telemetry_alerts(db, telemetry)

        assert alerts == []

    finally:
        _cleanup(db)
        db.close()


def test_high_dwell_alert_created():
    db = SessionLocal()
    service = AlertService()

    try:
        _cleanup(db)
        _create_test_truck(db)

        dwell_event = DwellEvent(
            load_id="TEST-LOAD-001",
            facility_name="Test Facility",
            broker_name="Test Broker",
        )

        alert = service.check_dwell_alert(
            db=db,
            dwell_event=dwell_event,
            dwell_hours=5.5,
            truck_id=TEST_TRUCK_ID,
        )

        assert alert is not None
        assert alert.alert_type == "high_dwell"
        assert alert.severity == "medium"

    finally:
        _cleanup(db)
        db.close()