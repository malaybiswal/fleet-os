from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.database import SessionLocal
from app.models.alert import Alert
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.services.operational_status import OperationalStatus
from app.services.telemetry_service import TelemetryService
from app.models.fleet import Fleet


TEST_TRUCK_ID = "TEST-TELEMETRY-TRUCK-001"
TEST_FLEET_ID = 999998
TEST_OTHER_FLEET_ID = 999997
TEST_FLEET_NAME = "Telemetry Service Test Fleet"


def _cleanup(db):
    db.query(Alert).filter(Alert.truck_id == TEST_TRUCK_ID).delete()
    db.query(TelemetryEvent).filter(TelemetryEvent.truck_id == TEST_TRUCK_ID).delete()
    db.query(Truck).filter(Truck.truck_id == TEST_TRUCK_ID).delete()
    db.query(Fleet).filter(
        Fleet.id.in_([TEST_FLEET_ID, TEST_OTHER_FLEET_ID])
    ).delete(synchronize_session=False)
    db.commit()


def _create_test_truck(db):
    fleet = Fleet(
        id=TEST_FLEET_ID,
        name=TEST_FLEET_NAME,
    )

    db.merge(fleet)
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


def test_ingest_telemetry_updates_truck_position():
    db = SessionLocal()
    service = TelemetryService()

    try:
        _cleanup(db)
        _create_test_truck(db)

        timestamp = datetime.now(timezone.utc)
        telemetry = TelemetryEvent(
            truck_id=TEST_TRUCK_ID,
            timestamp=timestamp,
            speed=Decimal("55.00"),
            fuel_level=Decimal("60.00"),
            engine_temp=Decimal("190.00"),
            gps_lat=Decimal("30.267200"),
            gps_lon=Decimal("-97.743100"),
            reefer_temp=Decimal("36.00"),
        )

        created = service.ingest_telemetry(db=db, telemetry_event=telemetry, fleet_id=TEST_FLEET_ID,)

        assert created.id is not None

        truck = db.query(Truck).filter(Truck.truck_id == TEST_TRUCK_ID).first()
        assert str(truck.current_lat) == "30.267200"
        assert str(truck.current_lon) == "-97.743100"
        assert truck.last_seen_at is not None
        assert truck.status == OperationalStatus.MOVING.value

    finally:
        _cleanup(db)
        db.close()


@pytest.mark.parametrize(
    ("speed", "expected_status"),
    [
        (Decimal("55.00"), OperationalStatus.MOVING.value),
        (Decimal("10.00"), OperationalStatus.SLOW.value),
        (Decimal("3.00"), OperationalStatus.IDLE.value),
        (Decimal("0.00"), OperationalStatus.STOPPED.value),
    ],
)
def test_ingest_telemetry_derives_truck_status_from_speed(speed, expected_status):
    db = SessionLocal()
    service = TelemetryService()

    try:
        _cleanup(db)
        _create_test_truck(db)

        telemetry = TelemetryEvent(
            truck_id=TEST_TRUCK_ID,
            timestamp=datetime.now(timezone.utc),
            speed=speed,
            fuel_level=Decimal("60.00"),
            engine_temp=Decimal("190.00"),
            gps_lat=Decimal("30.267200"),
            gps_lon=Decimal("-97.743100"),
            reefer_temp=Decimal("36.00"),
        )

        service.ingest_telemetry(
            db=db,
            telemetry_event=telemetry,
            fleet_id=TEST_FLEET_ID,
        )

        truck = db.query(Truck).filter(Truck.truck_id == TEST_TRUCK_ID).first()
        assert truck.status == expected_status

    finally:
        _cleanup(db)
        db.close()


def test_ingest_telemetry_triggers_low_fuel_alert():
    db = SessionLocal()
    service = TelemetryService()

    try:
        _cleanup(db)
        _create_test_truck(db)

        telemetry = TelemetryEvent(
            truck_id=TEST_TRUCK_ID,
            timestamp=datetime.now(timezone.utc),
            speed=Decimal("55.00"),
            fuel_level=Decimal("10.00"),
            engine_temp=Decimal("190.00"),
            gps_lat=Decimal("30.267200"),
            gps_lon=Decimal("-97.743100"),
            reefer_temp=Decimal("36.00"),
        )

        service.ingest_telemetry(db=db, telemetry_event=telemetry, fleet_id=TEST_FLEET_ID,)

        alert = (
            db.query(Alert)
            .filter(
                Alert.truck_id == TEST_TRUCK_ID,
                Alert.alert_type == "low_fuel",
                Alert.resolved.is_(False),
            )
            .first()
        )

        assert alert is not None
        assert alert.severity == "medium"
        assert alert.fleet_id == TEST_FLEET_ID

    finally:
        _cleanup(db)
        db.close()


def test_ingest_telemetry_unknown_truck_returns_404():
    db = SessionLocal()
    service = TelemetryService()

    try:
        telemetry = TelemetryEvent(
            truck_id="DOES-NOT-EXIST",
            timestamp=datetime.now(timezone.utc),
            fuel_level=Decimal("50.00"),

        )

        with pytest.raises(HTTPException) as exc_info:
            service.ingest_telemetry(db=db, telemetry_event=telemetry, fleet_id=TEST_FLEET_ID,)

        assert exc_info.value.status_code == 404

    finally:
        db.close()


def test_get_telemetry_for_truck_filters_history_by_fleet_id():
    db = SessionLocal()
    service = TelemetryService()
    base_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    try:
        _cleanup(db)
        _create_test_truck(db)
        db.merge(
            Fleet(
                id=TEST_OTHER_FLEET_ID,
                name="Other Telemetry Service Test Fleet",
            )
        )
        db.commit()

        visible_event = TelemetryEvent(
            truck_id=TEST_TRUCK_ID,
            fleet_id=TEST_FLEET_ID,
            timestamp=base_time,
            speed=Decimal("25.00"),
        )
        leaked_fleet_event = TelemetryEvent(
            truck_id=TEST_TRUCK_ID,
            fleet_id=TEST_OTHER_FLEET_ID,
            timestamp=base_time + timedelta(minutes=5),
            speed=Decimal("99.00"),
        )
        db.add_all([visible_event, leaked_fleet_event])
        db.commit()

        history = service.get_telemetry_for_truck(
            db=db,
            truck_id=TEST_TRUCK_ID,
            fleet_id=TEST_FLEET_ID,
        )

        assert [event.id for event in history] == [visible_event.id]

    finally:
        _cleanup(db)
        db.close()


def test_get_telemetry_for_truck_filters_history_by_timestamp_window():
    db = SessionLocal()
    service = TelemetryService()
    base_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    try:
        _cleanup(db)
        _create_test_truck(db)

        events = [
            TelemetryEvent(
                truck_id=TEST_TRUCK_ID,
                fleet_id=TEST_FLEET_ID,
                timestamp=base_time + timedelta(minutes=minutes),
                speed=Decimal(str(minutes)),
            )
            for minutes in [0, 5, 10, 15]
        ]
        db.add_all(events)
        db.commit()

        history = service.get_telemetry_for_truck(
            db=db,
            truck_id=TEST_TRUCK_ID,
            fleet_id=TEST_FLEET_ID,
            start_time=base_time + timedelta(minutes=5),
            end_time=base_time + timedelta(minutes=10),
        )

        assert [int(event.speed) for event in history] == [10, 5]

    finally:
        _cleanup(db)
        db.close()
