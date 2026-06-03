from datetime import datetime, timezone
from decimal import Decimal

from app.database import SessionLocal
from app.models.alert import Alert
from app.models.dwell_event import DwellEvent
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.services.alert_service import AlertService, AlertType
from app.models.fleet import Fleet


TEST_TRUCK_ID = "TEST-ALERT-TRUCK-001"
TEST_FLEET_ID = 999998
TEST_FLEET_NAME = "Alert Service Test Fleet"


def _cleanup(db):
    db.query(Alert).filter(Alert.truck_id == TEST_TRUCK_ID).delete()
    db.query(Truck).filter(Truck.truck_id == TEST_TRUCK_ID).delete()
    db.commit()


def _create_test_truck(db):
    fleet = Fleet(
        id=TEST_FLEET_ID,
        name=TEST_FLEET_NAME,
    )
    db.merge(fleet)
    db.commit()
    truck = Truck(
        truck_id=TEST_TRUCK_ID,
        fleet_id=TEST_FLEET_ID,
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

        alerts = service.check_telemetry_alerts(db=db, fleet_id=TEST_FLEET_ID, telemetry_event=telemetry)

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

        alerts = service.check_telemetry_alerts(db=db, fleet_id=TEST_FLEET_ID, telemetry_event=telemetry)

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

        alerts = service.check_telemetry_alerts(db=db, fleet_id=TEST_FLEET_ID, telemetry_event=telemetry)

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

        first = service.check_telemetry_alerts(db=db, fleet_id=TEST_FLEET_ID, telemetry_event=telemetry)
        second = service.check_telemetry_alerts(db=db, fleet_id=TEST_FLEET_ID, telemetry_event=telemetry)

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

        alerts = service.check_telemetry_alerts(db=db, fleet_id=TEST_FLEET_ID, telemetry_event=telemetry)

        assert alerts == []

    finally:
        _cleanup(db)
        db.close()


def test_alert_type_constants_exist():
    assert AlertType.LOW_FUEL == "low_fuel"
    assert AlertType.ENGINE_OVERHEAT == "engine_overheat"
    assert AlertType.REEFER_TEMP_DEVIATION == "reefer_temp_deviation"
    assert AlertType.HIGH_DWELL == "high_dwell"
    assert AlertType.SPEEDING == "speeding"
    assert AlertType.MAINTENANCE == "maintenance"
    assert AlertType.IDLE_TOO_LONG == "idle_too_long"


def test_check_status_alerts_returns_empty_list():
    db = SessionLocal()
    service = AlertService()

    try:
        _cleanup(db)
        _create_test_truck(db)

        result = service.check_status_alerts(
            db=db,
            fleet_id=TEST_FLEET_ID,
            truck_id=TEST_TRUCK_ID,
            operational_status="moving",
        )

        assert result == []

    finally:
        _cleanup(db)
        db.close()


def test_evaluate_telemetry_alerts_delegates_to_sub_methods():
    """evaluate_telemetry_alerts() is the single call site — verify it
    runs both check_telemetry_alerts and check_status_alerts and returns
    their combined results."""
    from unittest.mock import MagicMock, patch

    service = AlertService()
    mock_event = MagicMock(spec=TelemetryEvent)
    mock_event.truck_id = TEST_TRUCK_ID

    sentinel_alert = MagicMock(spec=Alert)

    with patch.object(service, "check_telemetry_alerts", return_value=[sentinel_alert]) as mock_telem, \
         patch.object(service, "check_status_alerts", return_value=[]) as mock_status:

        result = service.evaluate_telemetry_alerts(
            db=MagicMock(),
            fleet_id=TEST_FLEET_ID,
            telemetry_event=mock_event,
            operational_status="moving",
        )

        mock_telem.assert_called_once()
        mock_status.assert_called_once()
        assert result == [sentinel_alert]


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
            fleet_id=TEST_FLEET_ID,
        )

        assert alert is not None
        assert alert.alert_type == "high_dwell"
        assert alert.severity == "medium"
        assert alert.fleet_id == TEST_FLEET_ID

    finally:
        _cleanup(db)
        db.close()