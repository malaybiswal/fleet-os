from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.database import SessionLocal
from app.models.alert import Alert
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.services.telemetry_service import TelemetryService
from app.models.fleet import Fleet


TEST_TRUCK_ID = "TEST-TELEMETRY-TRUCK-001"
TEST_FLEET_ID = 999998
TEST_FLEET_NAME = "Telemetry Service Test Fleet"


def _cleanup(db):
    db.query(Alert).filter(Alert.truck_id == TEST_TRUCK_ID).delete()
    db.query(TelemetryEvent).filter(TelemetryEvent.truck_id == TEST_TRUCK_ID).delete()
    db.query(Truck).filter(Truck.truck_id == TEST_TRUCK_ID).delete()
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