from fastapi.testclient import TestClient

from app.dependencies.fleet import get_current_fleet_id
from app.main import app
from app.models.driver import Driver
from app.models.dwell_event import DwellEvent
from app.models.facility import Facility
from app.models.fleet import Fleet
from app.models.load import Load
from app.models.truck import Truck

client = TestClient(app)


def test_get_dwell_events():
    response = client.get("/api/dwell/events")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_facility_scorecard():
    response = client.get("/api/dwell/facility-scorecard")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_broker_scorecard():
    response = client.get("/api/dwell/broker-scorecard")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_dwell_event_upserts_facility(client, db):
    fleet = Fleet(name="Dwell Upsert Fleet")
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet.id

    db.add_all(
        [
            Truck(truck_id="DWELL-TRK-1", fleet_id=fleet.id, status="moving"),
            Driver(driver_id="DWELL-DRV-1", name="Dwell Driver", status="active", fleet_id=fleet.id),
        ]
    )
    db.commit()
    db.add(
        Load(
            load_id="DWELL-LOAD-1",
            truck_id="DWELL-TRK-1",
            driver_id="DWELL-DRV-1",
            status="delivered",
            fleet_id=fleet.id,
        )
    )
    db.commit()

    response = client.post(
        "/api/dwell",
        json={
            "load_id": "DWELL-LOAD-1",
            "facility_name": "Brand New Facility",
            "arrival_time": "2026-06-01T08:00:00",
            "departure_time": "2026-06-01T10:00:00",
        },
    )

    assert response.status_code == 201

    facility = (
        db.query(Facility)
        .filter(Facility.fleet_id == fleet.id, Facility.normalized_name == "brand new facility")
        .first()
    )
    assert facility is not None

    event = db.query(DwellEvent).filter(DwellEvent.load_id == "DWELL-LOAD-1").first()
    assert event.facility_id == facility.id

    # Same name reuses the same facility row.
    response = client.post(
        "/api/dwell",
        json={
            "load_id": "DWELL-LOAD-1",
            "facility_name": "  brand NEW   facility ",
            "arrival_time": "2026-06-02T08:00:00",
            "departure_time": "2026-06-02T09:00:00",
        },
    )
    assert response.status_code == 201
    assert db.query(Facility).filter(Facility.fleet_id == fleet.id).count() == 1