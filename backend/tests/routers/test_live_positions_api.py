from datetime import datetime, timezone
from app.config import settings
from app.models.fleet import Fleet
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.main import app
from app.dependencies.fleet import get_current_fleet_id


def test_get_live_positions_returns_fleet_trucks(client, db):
    fleet = Fleet(name="Live Fleet")
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    settings.DEV_FLEET_ID = fleet.id
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet.id

    truck = Truck(
        truck_id="LIVE-001",
        status="moving",
        fleet_id=fleet.id,
        current_location="Austin, TX",
        current_lat=30.2672,
        current_lon=-97.7431,
        last_seen_at=datetime.now(timezone.utc),
    )
    db.add(truck)
    db.commit()

    telemetry_event = TelemetryEvent(
        truck_id="LIVE-001",
        fleet_id=fleet.id,
        timestamp=datetime.now(timezone.utc),
        speed=55.5,
        gps_lat=30.2672,
        gps_lon=-97.7431,
    )
    db.add(telemetry_event)
    db.commit()

    response = client.get("/api/fleet/live-positions")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["truck_id"] == "LIVE-001"
    assert data[0]["status"] == "moving"
    assert data[0]["latitude"] == 30.2672
    assert data[0]["longitude"] == -97.7431
    assert data[0]["speed"] == 55.5
    assert data[0]["current_location"] == "Austin, TX"
    app.dependency_overrides.clear()


def test_get_live_positions_does_not_return_other_fleet_trucks(client, db):
    fleet = Fleet(name="Live Fleet 2")
    other_fleet = Fleet(name="Other Fleet 2")
    db.add_all([fleet, other_fleet])
    db.commit()
    db.refresh(fleet)
    db.refresh(other_fleet)
    settings.DEV_FLEET_ID = fleet.id
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet.id

    visible_truck = Truck(
        truck_id="LIVE-002",
        status="moving",
        fleet_id=fleet.id,
        current_location="Dallas, TX",
        current_lat=32.7767,
        current_lon=-96.7970,
        last_seen_at=datetime.now(timezone.utc),
    )

    hidden_truck = Truck(
        truck_id="HIDDEN-001",
        status="moving",
        fleet_id=other_fleet.id,
        current_location="Houston, TX",
        current_lat=29.7604,
        current_lon=-95.3698,
        last_seen_at=datetime.now(timezone.utc),
    )

    db.add_all([visible_truck, hidden_truck])
    db.commit()

    response = client.get("/api/fleet/live-positions")

    assert response.status_code == 200

    truck_ids = {truck["truck_id"] for truck in response.json()}

    assert "LIVE-002" in truck_ids
    assert "HIDDEN-001" not in truck_ids
    app.dependency_overrides.clear()
