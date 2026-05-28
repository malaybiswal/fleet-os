from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.alert import Alert
from app.models.fleet import Fleet
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.repositories.alert_repository import AlertRepository
from app.repositories.telemetry_repository import TelemetryRepository


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def _create_fleet(db, name: str) -> Fleet:
    fleet = Fleet(name=name)
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    return fleet


def _create_truck(db, fleet: Fleet, truck_id: str) -> Truck:
    truck = Truck(
        truck_id=truck_id,
        fleet_id=fleet.id,
        status="moving",
    )
    db.add(truck)
    db.commit()
    db.refresh(truck)
    return truck


def test_telemetry_and_alert_models_define_history_indexes():
    telemetry_indexes = {
        index.name: tuple(column.name for column in index.columns)
        for index in TelemetryEvent.__table__.indexes
    }
    alert_indexes = {
        index.name: tuple(column.name for column in index.columns)
        for index in Alert.__table__.indexes
    }

    assert telemetry_indexes["idx_telemetry_truck_time"] == (
        "truck_id",
        "timestamp",
    )
    assert telemetry_indexes["idx_telemetry_fleet_time"] == (
        "fleet_id",
        "timestamp",
    )
    assert alert_indexes["idx_alerts_fleet_created_at"] == (
        "fleet_id",
        "created_at",
    )


def test_get_latest_positions_returns_one_latest_event_per_fleet_truck():
    db = TestingSessionLocal()
    repo = TelemetryRepository()
    base_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    try:
        fleet = _create_fleet(db, "Latest Position Fleet")
        other_fleet = _create_fleet(db, "Other Latest Position Fleet")
        _create_truck(db, fleet, "TRK-LATEST-001")
        _create_truck(db, fleet, "TRK-LATEST-002")
        _create_truck(db, other_fleet, "TRK-LATEST-HIDDEN")

        older_event = TelemetryEvent(
            truck_id="TRK-LATEST-001",
            fleet_id=fleet.id,
            timestamp=base_time,
            speed=10,
        )
        lower_id_tie = TelemetryEvent(
            truck_id="TRK-LATEST-001",
            fleet_id=fleet.id,
            timestamp=base_time + timedelta(minutes=5),
            speed=20,
        )
        higher_id_tie = TelemetryEvent(
            truck_id="TRK-LATEST-001",
            fleet_id=fleet.id,
            timestamp=base_time + timedelta(minutes=5),
            speed=30,
        )
        second_truck_event = TelemetryEvent(
            truck_id="TRK-LATEST-002",
            fleet_id=fleet.id,
            timestamp=base_time + timedelta(minutes=1),
            speed=40,
        )
        hidden_event = TelemetryEvent(
            truck_id="TRK-LATEST-HIDDEN",
            fleet_id=other_fleet.id,
            timestamp=base_time + timedelta(minutes=10),
            speed=99,
        )
        db.add_all(
            [
                older_event,
                lower_id_tie,
                higher_id_tie,
                second_truck_event,
                hidden_event,
            ]
        )
        db.commit()

        latest_positions = repo.get_latest_positions(db, fleet.id)
        latest_by_truck_id = {
            event.truck_id: event for event in latest_positions
        }

        assert set(latest_by_truck_id) == {
            "TRK-LATEST-001",
            "TRK-LATEST-002",
        }
        assert latest_by_truck_id["TRK-LATEST-001"].id == higher_id_tie.id
        assert latest_by_truck_id["TRK-LATEST-002"].id == second_truck_event.id

    finally:
        db.close()


def test_get_truck_history_filters_by_fleet_truck_timestamp_and_pagination():
    db = TestingSessionLocal()
    repo = TelemetryRepository()
    base_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    try:
        fleet = _create_fleet(db, "History Fleet")
        other_fleet = _create_fleet(db, "Other History Fleet")
        _create_truck(db, fleet, "TRK-HISTORY-001")

        events = [
            TelemetryEvent(
                truck_id="TRK-HISTORY-001",
                fleet_id=fleet.id,
                timestamp=base_time + timedelta(minutes=minutes),
                speed=minutes,
            )
            for minutes in [0, 5, 10, 15]
        ]
        leaked_fleet_event = TelemetryEvent(
            truck_id="TRK-HISTORY-001",
            fleet_id=other_fleet.id,
            timestamp=base_time + timedelta(minutes=20),
            speed=99,
        )
        db.add_all([*events, leaked_fleet_event])
        db.commit()

        history = repo.get_truck_history(
            db=db,
            fleet_id=fleet.id,
            truck_id="TRK-HISTORY-001",
            start_time=base_time + timedelta(minutes=5),
            end_time=base_time + timedelta(minutes=15),
            limit=2,
            offset=1,
        )

        assert [int(event.speed) for event in history] == [10, 5]
        assert {event.fleet_id for event in history} == {fleet.id}

    finally:
        db.close()


def test_get_recent_alert_window_filters_by_fleet_time_truck_type_and_resolution():
    db = TestingSessionLocal()
    repo = AlertRepository()
    base_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    try:
        fleet = _create_fleet(db, "Alert Window Fleet")
        other_fleet = _create_fleet(db, "Other Alert Window Fleet")
        _create_truck(db, fleet, "TRK-ALERT-001")
        _create_truck(db, fleet, "TRK-ALERT-002")

        matching_alert = Alert(
            truck_id="TRK-ALERT-001",
            fleet_id=fleet.id,
            severity="medium",
            alert_type="low_fuel",
            message="Fuel low",
            created_at=base_time + timedelta(minutes=5),
            resolved=False,
        )
        wrong_type_alert = Alert(
            truck_id="TRK-ALERT-001",
            fleet_id=fleet.id,
            severity="high",
            alert_type="engine_overheat",
            message="Engine hot",
            created_at=base_time + timedelta(minutes=10),
            resolved=False,
        )
        wrong_truck_alert = Alert(
            truck_id="TRK-ALERT-002",
            fleet_id=fleet.id,
            severity="medium",
            alert_type="low_fuel",
            message="Fuel low",
            created_at=base_time + timedelta(minutes=12),
            resolved=False,
        )
        resolved_alert = Alert(
            truck_id="TRK-ALERT-001",
            fleet_id=fleet.id,
            severity="medium",
            alert_type="low_fuel",
            message="Fuel low",
            created_at=base_time + timedelta(minutes=15),
            resolved=True,
        )
        other_fleet_alert = Alert(
            truck_id="TRK-ALERT-001",
            fleet_id=other_fleet.id,
            severity="medium",
            alert_type="low_fuel",
            message="Fuel low",
            created_at=base_time + timedelta(minutes=20),
            resolved=False,
        )
        db.add_all(
            [
                matching_alert,
                wrong_type_alert,
                wrong_truck_alert,
                resolved_alert,
                other_fleet_alert,
            ]
        )
        db.commit()

        alerts = repo.get_recent_alert_window(
            db=db,
            fleet_id=fleet.id,
            start_time=base_time,
            end_time=base_time + timedelta(minutes=20),
            truck_id="TRK-ALERT-001",
            alert_type="low_fuel",
            resolved=False,
        )

        assert [alert.id for alert in alerts] == [matching_alert.id]

    finally:
        db.close()
