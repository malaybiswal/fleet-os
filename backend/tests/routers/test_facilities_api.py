from datetime import datetime, timedelta

from app.dependencies.fleet import get_current_fleet_id
from app.main import app
from app.models.driver import Driver
from app.models.dwell_event import DwellEvent
from app.models.facility import Facility, normalize_facility_name
from app.models.fleet import Fleet
from app.models.load import Load
from app.models.truck import Truck


def _create_fleet(db, name: str) -> Fleet:
    fleet = Fleet(name=name)
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    return fleet


def _create_facility(db, fleet: Fleet, name: str) -> Facility:
    facility = Facility(
        fleet_id=fleet.id,
        name=name,
        normalized_name=normalize_facility_name(name),
    )
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return facility


def _create_load(db, fleet: Fleet, load_id: str) -> Load:
    if db.query(Truck).filter(Truck.truck_id == f"FAC-TRK-{fleet.id}").first() is None:
        db.add_all(
            [
                Truck(truck_id=f"FAC-TRK-{fleet.id}", fleet_id=fleet.id, status="moving"),
                Driver(
                    driver_id=f"FAC-DRV-{fleet.id}",
                    name="Facility Test Driver",
                    status="active",
                    fleet_id=fleet.id,
                ),
            ]
        )
        db.commit()
    load = Load(
        load_id=load_id,
        truck_id=f"FAC-TRK-{fleet.id}",
        driver_id=f"FAC-DRV-{fleet.id}",
        status="delivered",
        fleet_id=fleet.id,
    )
    db.add(load)
    db.commit()
    return load


def _create_visit(
    db,
    fleet: Fleet,
    facility: Facility,
    load_id: str,
    dwell_hours: float,
    arrival: datetime,
    appointment_delay_minutes: int | None = None,
    detention_pay: float | None = None,
):
    _create_load(db, fleet, load_id)
    appointment_time = None
    loading_start = None
    if appointment_delay_minutes is not None:
        appointment_time = arrival + timedelta(minutes=15)
        loading_start = appointment_time + timedelta(minutes=appointment_delay_minutes)
    db.add(
        DwellEvent(
            load_id=load_id,
            fleet_id=fleet.id,
            facility_id=facility.id,
            facility_name=facility.name,
            appointment_time=appointment_time,
            arrival_time=arrival,
            loading_start=loading_start,
            departure_time=arrival + timedelta(hours=dwell_hours),
            detention_pay=detention_pay,
        )
    )
    db.commit()


def _use_fleet(fleet: Fleet):
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet.id


def test_list_facilities_empty_fleet(client, db):
    fleet = _create_fleet(db, "Empty Facilities Fleet")
    _use_fleet(fleet)

    response = client.get("/api/facilities")

    assert response.status_code == 200
    assert response.json() == []


def test_list_facilities_returns_intelligence_worst_first(client, db):
    fleet = _create_fleet(db, "Facilities Fleet")
    _use_fleet(fleet)
    good = _create_facility(db, fleet, "Fast Crossdock")
    bad = _create_facility(db, fleet, "Slow Cold Storage")

    base = datetime(2026, 6, 1, 8, 0)
    for index in range(3):
        _create_visit(
            db, fleet, good, f"GOOD-{index}", 1.0,
            base + timedelta(days=index), appointment_delay_minutes=0,
        )
        _create_visit(
            db, fleet, bad, f"BAD-{index}", 7.0,
            base + timedelta(days=index), appointment_delay_minutes=120,
            detention_pay=375.0,
        )

    response = client.get("/api/facilities")

    assert response.status_code == 200
    data = response.json()
    assert [item["facility_name"] for item in data] == ["Slow Cold Storage", "Fast Crossdock"]

    worst = data[0]
    assert worst["facility_id"] == bad.id
    assert worst["visit_count"] == 3
    assert worst["confidence"] == "medium"
    assert worst["detention_risk_band"] == "high"
    assert worst["appointment_reliability_pct"] == 0.0
    assert worst["avg_dwell_hours"] == 7.0
    assert float(worst["total_detention_pay"]) == 1125.0

    best = data[1]
    assert best["detention_risk_band"] == "low"
    assert best["appointment_reliability_pct"] == 100.0
    assert best["operational_score"] > worst["operational_score"]


def test_list_facilities_date_filter(client, db):
    fleet = _create_fleet(db, "Date Filter Fleet")
    _use_fleet(fleet)
    facility = _create_facility(db, fleet, "Seasonal Yard")
    _create_visit(db, fleet, facility, "OLD-1", 2.0, datetime(2026, 1, 1, 8, 0))
    _create_visit(db, fleet, facility, "NEW-1", 2.0, datetime(2026, 6, 1, 8, 0))

    response = client.get("/api/facilities", params={"start_date": "2026-03-01T00:00:00"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["visit_count"] == 1


def test_get_facility_detail(client, db):
    fleet = _create_fleet(db, "Detail Fleet")
    _use_fleet(fleet)
    facility = _create_facility(db, fleet, "Detail DC")
    _create_visit(db, fleet, facility, "DETAIL-1", 3.0, datetime(2026, 6, 1, 8, 0))

    response = client.get(f"/api/facilities/{facility.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["facility_id"] == facility.id
    assert data["facility_name"] == "Detail DC"
    assert data["visit_count"] == 1
    assert len(data["recent_dwell_events"]) == 1
    assert data["recent_dwell_events"][0]["load_id"] == "DETAIL-1"


def test_get_facility_detail_cross_fleet_404(client, db):
    fleet_a = _create_fleet(db, "Owner Fleet")
    fleet_b = _create_fleet(db, "Other Fleet")
    facility = _create_facility(db, fleet_a, "Private DC")
    _use_fleet(fleet_b)

    response = client.get(f"/api/facilities/{facility.id}")

    assert response.status_code == 404
