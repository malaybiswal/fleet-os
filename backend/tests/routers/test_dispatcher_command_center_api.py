from app.dependencies.fleet import get_current_fleet_id
from app.main import app
from app.models.driver import Driver
from app.models.fleet import Fleet
from app.models.load import Load
from app.models.truck import Truck
from app.seed.mock_fleets import DEFAULT_BASE_DATE, DEFAULT_DEMO_SEED
from app.seed.persist import reset_demo_environment
from app.repositories.load_repository import CANDIDATE_STATUSES


def _seed_decision_load(
    db,
    *,
    suffix: str,
    fleet: Fleet | None = None,
    revenue=3000,
    miles=1000,
    deadhead_miles=50,
    status="booked",
    assigned=True,
):
    if fleet is None:
        fleet = Fleet(name=f"Command Center Fleet {suffix}")
        db.add(fleet)
        db.commit()
        db.refresh(fleet)

    truck = Truck(
        truck_id=f"CC-TRUCK-{suffix}",
        status="moving",
        current_location="Dallas yard",
        current_lat=32.7767,
        current_lon=-96.797,
        fleet_id=fleet.id,
    )
    driver = Driver(
        driver_id=f"CC-DRIVER-{suffix}",
        name=f"Command Center Driver {suffix}",
        status="available",
        hos_hours_remaining=8.0,
        fleet_id=fleet.id,
    )
    load = Load(
        load_id=f"CC-LOAD-{suffix}",
        truck_id=truck.truck_id if assigned else None,
        driver_id=driver.driver_id if assigned else None,
        broker_name="Demo Broker",
        origin="Dallas, TX",
        destination="Houston, TX",
        revenue=revenue,
        miles=miles,
        deadhead_miles=deadhead_miles,
        fuel_cost=400,
        maintenance_reserve=120,
        driver_cost=720,
        tolls=25,
        equipment_type="Dry Van",
        status=status,
        fleet_id=fleet.id,
    )
    db.add_all([truck, driver, load])
    db.commit()
    db.refresh(load)
    return fleet, load


def _seed_candidate_load(db, *, load_id: str, fleet: Fleet) -> Load:
    load = Load(
        load_id=load_id,
        truck_id=None,
        driver_id=None,
        broker_name="Test Broker",
        origin="Dallas, TX",
        destination="Houston, TX",
        revenue=950,
        miles=260,
        deadhead_miles=20,
        status="available",
        fleet_id=fleet.id,
        equipment_type="Dry Van",
    )
    db.add(load)
    db.commit()
    db.refresh(load)
    return load


def test_get_candidates_returns_only_available_loads(client, db):
    fleet, booked_load = _seed_decision_load(db, suffix="CAND-FILTER")
    candidate = _seed_candidate_load(db, load_id="CAND-LOAD-TEST", fleet=fleet)
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet.id

    try:
        response = client.get("/api/dispatcher-command-center/candidates")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    ids = {item["load_id"] for item in response.json()}
    assert candidate.load_id in ids
    assert booked_load.load_id not in ids
    for item in response.json():
        assert item["status"] in CANDIDATE_STATUSES


def test_get_candidates_is_fleet_scoped(client, db):
    fleet_a, _ = _seed_decision_load(db, suffix="SCOPE-A")
    fleet_b = Fleet(name="Other Fleet Scope Test P1")
    db.add(fleet_b)
    db.commit()
    db.refresh(fleet_b)
    _seed_candidate_load(db, load_id="CAND-OTHER-FLEET-P1", fleet=fleet_b)
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet_a.id

    try:
        response = client.get("/api/dispatcher-command-center/candidates")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    ids = {item["load_id"] for item in response.json()}
    assert "CAND-OTHER-FLEET-P1" not in ids


def test_seeded_demo_candidate_loads_appear_in_candidates_endpoint(client, db):
    result = reset_demo_environment(db, seed=DEFAULT_DEMO_SEED, base_date=DEFAULT_BASE_DATE)
    operations_fleet_id = result.fleet_ids["operations"]
    app.dependency_overrides[get_current_fleet_id] = lambda: operations_fleet_id

    try:
        response = client.get("/api/dispatcher-command-center/candidates")
    finally:
        app.dependency_overrides.pop(get_current_fleet_id, None)

    assert response.status_code == 200
    ids = {item["load_id"] for item in response.json()}
    assert ids == {"DEMO-CAND-GOOD", "DEMO-CAND-WEAK-BROKER", "DEMO-CAND-BAD-DEADHEAD"}
    for item in response.json():
        assert item["truck_id"] is None
        assert item["driver_id"] is None
        assert item["equipment_type"] is not None


def test_get_dispatcher_decision_returns_ranked_backend_contract(client, db):
    fleet, load = _seed_decision_load(
        db,
        suffix="SUCCESS",
        status="available",
        assigned=False,
    )
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet.id

    try:
        response = client.get(
            f"/api/dispatcher-command-center/loads/{load.load_id}/decision"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()

    assert body["load"]["load_id"] == load.load_id
    assert body["final_recommendation"] == "RECOMMENDED"
    assert body["metrics"]["profitability_score"] > 0
    assert body["metrics"]["final_dispatch_score"] == body["best_truck"]["rank_score"]
    assert body["best_truck"]["truck_id"] == f"CC-TRUCK-SUCCESS"
    assert body["best_truck"]["driver_id"] == f"CC-DRIVER-SUCCESS"
    assert body["best_truck"]["driver_name"] == "Command Center Driver SUCCESS"
    assert body["best_truck"]["driver_hos_hours_remaining"] == 8.0
    assert body["truck_options"][0]["truck_id"] == f"CC-TRUCK-SUCCESS"
    assert body["metrics"]["deadhead_miles"] == 50
    assert body["metrics"]["estimated_revenue_per_hour"] > 0
    assert body["decision_notes"]


def test_get_dispatcher_decision_returns_404_for_missing_load(client, db):
    fleet = Fleet(name="Command Center Missing Fleet")
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet.id

    try:
        response = client.get(
            "/api/dispatcher-command-center/loads/DOES-NOT-EXIST/decision"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"] == "Load DOES-NOT-EXIST not found"


def test_get_dispatcher_decision_returns_404_for_other_fleet_load(client, db):
    current_fleet = Fleet(name="Command Center Current Fleet")
    other_fleet = Fleet(name="Command Center Other Fleet")
    db.add_all([current_fleet, other_fleet])
    db.commit()
    db.refresh(current_fleet)
    db.refresh(other_fleet)
    _, other_load = _seed_decision_load(db, suffix="OTHER", fleet=other_fleet)
    app.dependency_overrides[get_current_fleet_id] = lambda: current_fleet.id

    try:
        response = client.get(
            f"/api/dispatcher-command-center/loads/{other_load.load_id}/decision"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"] == f"Load {other_load.load_id} not found"


def test_get_dispatcher_decision_returns_422_for_invalid_load_economics(client, db):
    fleet, load = _seed_decision_load(
        db,
        suffix="INVALID",
        revenue=0,
        miles=1000,
        deadhead_miles=50,
    )
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet.id

    try:
        response = client.get(
            f"/api/dispatcher-command-center/loads/{load.load_id}/decision"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"] == "Load revenue must be greater than 0"


def test_accept_recommendation_assigns_candidate_load(client, db):
    fleet, load = _seed_decision_load(
        db,
        suffix="ASSIGN",
        status="available",
        assigned=False,
    )
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet.id

    try:
        response = client.post(
            f"/api/dispatcher-command-center/loads/{load.load_id}/assign",
            json={
                "truck_id": "CC-TRUCK-ASSIGN",
                "driver_id": "CC-DRIVER-ASSIGN",
            },
        )
        candidates_response = client.get("/api/dispatcher-command-center/candidates")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["load_id"] == load.load_id
    assert body["truck_id"] == "CC-TRUCK-ASSIGN"
    assert body["driver_id"] == "CC-DRIVER-ASSIGN"
    assert body["status"] == "booked"

    db.refresh(load)
    assert load.truck_id == "CC-TRUCK-ASSIGN"
    assert load.driver_id == "CC-DRIVER-ASSIGN"
    assert load.status == "booked"
    assert load.load_id not in {item["load_id"] for item in candidates_response.json()}


def test_accept_recommendation_returns_409_for_booked_load(client, db):
    fleet, load = _seed_decision_load(
        db,
        suffix="ALREADY-BOOKED",
        status="booked",
        assigned=True,
    )
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet.id

    try:
        response = client.post(
            f"/api/dispatcher-command-center/loads/{load.load_id}/assign",
            json={
                "truck_id": "CC-TRUCK-ALREADY-BOOKED",
                "driver_id": "CC-DRIVER-ALREADY-BOOKED",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "already booked" in response.json()["error"]


def test_accept_recommendation_returns_409_for_busy_truck(client, db):
    fleet, load = _seed_decision_load(
        db,
        suffix="BUSY-TRUCK",
        status="available",
        assigned=False,
    )
    db.add(
        Load(
            load_id="CC-LOAD-BUSY-TRUCK-ACTIVE",
            truck_id="CC-TRUCK-BUSY-TRUCK",
            driver_id=None,
            broker_name="Demo Broker",
            origin="Dallas, TX",
            destination="Austin, TX",
            revenue=1000,
            miles=200,
            deadhead_miles=10,
            status="booked",
            fleet_id=fleet.id,
            equipment_type="Dry Van",
        )
    )
    db.commit()
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet.id

    try:
        response = client.post(
            f"/api/dispatcher-command-center/loads/{load.load_id}/assign",
            json={
                "truck_id": "CC-TRUCK-BUSY-TRUCK",
                "driver_id": "CC-DRIVER-BUSY-TRUCK",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "no longer available" in response.json()["error"]


def test_accept_recommendation_returns_404_for_other_fleet_load(client, db):
    current_fleet = Fleet(name="Command Center Assign Current Fleet")
    other_fleet = Fleet(name="Command Center Assign Other Fleet")
    db.add_all([current_fleet, other_fleet])
    db.commit()
    db.refresh(current_fleet)
    db.refresh(other_fleet)
    _, other_load = _seed_decision_load(
        db,
        suffix="ASSIGN-OTHER",
        fleet=other_fleet,
        status="available",
        assigned=False,
    )
    app.dependency_overrides[get_current_fleet_id] = lambda: current_fleet.id

    try:
        response = client.post(
            f"/api/dispatcher-command-center/loads/{other_load.load_id}/assign",
            json={
                "truck_id": "CC-TRUCK-ASSIGN-OTHER",
                "driver_id": "CC-DRIVER-ASSIGN-OTHER",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"] == f"Load {other_load.load_id} not found"


def test_seeded_operations_demo_loads_match_command_center_story(client, db):
    result = reset_demo_environment(
        db,
        seed=DEFAULT_DEMO_SEED,
        base_date=DEFAULT_BASE_DATE,
    )
    operations_fleet_id = result.fleet_ids["operations"]
    app.dependency_overrides[get_current_fleet_id] = lambda: operations_fleet_id

    try:
        loads_response = client.get("/api/loads")
        assert loads_response.status_code == 200

        loads_by_id = {load["load_id"]: load for load in loads_response.json()}
        expected = {
            "DEMO-CAND-GOOD": "RECOMMENDED",
            "DEMO-CAND-WEAK-BROKER": {"RECOMMENDED", "REVIEW"},
            "DEMO-CAND-BAD-DEADHEAD": "AVOID",
        }

        for load_id, recommendation in expected.items():
            decision_response = client.get(
                f"/api/dispatcher-command-center/loads/{load_id}/decision"
            )
            assert decision_response.status_code == 200

            load = loads_by_id[load_id]
            decision = decision_response.json()

            assert decision["load"]["load_id"] == load_id
            if isinstance(recommendation, set):
                assert decision["final_recommendation"] in recommendation
            else:
                assert decision["final_recommendation"] == recommendation
            assert decision["facility_risk"] == load["facility_risk"]
            assert decision["best_truck"] is not None
            assert decision["best_truck"]["driver_id"] not in {
                "DEMO-DRIVER-002",
                "DEMO-DRIVER-004",
                "DEMO-DRIVER-005",
            }
            assert decision["best_truck"]["driver_hos_hours_remaining"] >= 2.0

        candidate_decision = client.get(
            "/api/dispatcher-command-center/loads/DEMO-CAND-GOOD/decision"
        ).json()
        assert {"DEMO-TRUCK-002", "DEMO-TRUCK-005", "DEMO-TRUCK-006"}.isdisjoint({
            option["truck_id"] for option in candidate_decision["truck_options"]
        })
        assert {"DEMO-DRIVER-002", "DEMO-DRIVER-004", "DEMO-DRIVER-005"}.isdisjoint({
            option["driver_id"] for option in candidate_decision["truck_options"]
        })
        assert all(
            option["driver_hos_hours_remaining"] >= 2.0
            for option in candidate_decision["truck_options"]
        )
    finally:
        app.dependency_overrides.pop(get_current_fleet_id, None)
