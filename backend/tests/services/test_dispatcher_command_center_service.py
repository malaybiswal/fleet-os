from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base
from app.schemas.facility import FacilityRiskSummary
from app.schemas.live_position import LiveTruckPosition
from app.seed.mock_fleets import DEFAULT_BASE_DATE, DEFAULT_DEMO_SEED
from app.seed.persist import reset_demo_environment
from app.services.dispatcher_command_center_service import (
    DispatcherAssignmentConflictError,
    DispatcherCommandCenterService,
    DEMO_SAFE_DEADHEAD_NOTE,
)
from app.services.deadhead import DEADHEAD_SOURCE_HAVERSINE, DEADHEAD_SOURCE_STORED_FALLBACK


class FakeLoadRepository:
    def __init__(
        self,
        load,
        busy_truck_ids: set[str] | None = None,
        busy_driver_ids: set[str] | None = None,
    ):
        self.load = load
        self.busy_truck_ids = busy_truck_ids or set()
        self.busy_driver_ids = busy_driver_ids or set()

    def get_by_id_and_fleet(self, db, load_id: str, fleet_id: int):
        if self.load.load_id == load_id and self.load.fleet_id == fleet_id:
            return self.load
        return None

    def get_active_assignments_by_fleet(self, db, fleet_id: int):
        return self.busy_truck_ids, self.busy_driver_ids

    def assign(self, db, load, truck_id: str, driver_id: str):
        load.truck_id = truck_id
        load.driver_id = driver_id
        load.status = "booked"
        return load


class FakeDriverRepository:
    def __init__(self, drivers):
        self.drivers = drivers

    def get_available_by_fleet(self, db, fleet_id: int, min_hos_hours: Decimal):
        return [
            driver
            for driver in self.drivers
            if driver.fleet_id == fleet_id
            and driver.status == "available"
            and (
                driver.hos_hours_remaining is None
                or Decimal(str(driver.hos_hours_remaining)) >= min_hos_hours
            )
        ]


class FakeFacilityService:
    def __init__(self, facility_risk: FacilityRiskSummary | None = None):
        self.facility_risk = facility_risk

    def get_facility_risk_by_load_id(self, db, fleet_id: int, load_ids: list[str]):
        if self.facility_risk is None:
            return {}
        return {load_ids[0]: self.facility_risk}


def _service(
    load,
    positions,
    facility_risk: FacilityRiskSummary | None = None,
    drivers=None,
    busy_truck_ids: set[str] | None = None,
    busy_driver_ids: set[str] | None = None,
):
    return DispatcherCommandCenterService(
        load_repository=FakeLoadRepository(load, busy_truck_ids, busy_driver_ids),
        driver_repository=FakeDriverRepository(drivers or [_driver()]),
        facility_service=FakeFacilityService(facility_risk),
        live_positions_provider=lambda db, fleet_id: positions,
    )


@pytest.fixture
def seeded_demo_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _load(
    *,
    revenue=3000,
    miles=1000,
    deadhead_miles=50,
    origin="Dallas, TX",
    origin_lat=None,
    origin_lon=None,
    broker_name="Demo Broker",
    truck_id="TRUCK-001",
    load_id="LOAD-001",
    fleet_id=1,
    status="booked",
):
    return SimpleNamespace(
        id=1,
        load_id=load_id,
        truck_id=truck_id,
        driver_id="DRIVER-001",
        equipment_type="Dry Van",
        broker_name=broker_name,
        origin=origin,
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        destination="Houston, TX",
        revenue=Decimal(str(revenue)),
        miles=Decimal(str(miles)),
        deadhead_miles=Decimal(str(deadhead_miles)),
        fuel_cost=Decimal("400"),
        maintenance_reserve=Decimal("120"),
        driver_cost=Decimal("720"),
        tolls=Decimal("25"),
        pickup_time=None,
        delivery_time=None,
        status=status,
        fleet_id=fleet_id,
    )


def _driver(
    driver_id: str = "DRIVER-001",
    *,
    name="Test Driver",
    status="available",
    hos_hours_remaining=Decimal("8.0"),
    fleet_id=1,
):
    return SimpleNamespace(
        driver_id=driver_id,
        name=name,
        status=status,
        hos_hours_remaining=hos_hours_remaining,
        fleet_id=fleet_id,
    )


def _position(
    truck_id: str,
    *,
    status="moving",
    current_location="Dallas yard",
    latitude=32.7767,
    longitude=-96.797,
    last_seen_at=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
    highest_alert_severity=None,
    active_alert_count=0,
):
    return LiveTruckPosition(
        truck_id=truck_id,
        status=status,
        latitude=latitude,
        longitude=longitude,
        speed=45,
        heading=90,
        last_seen_at=last_seen_at,
        current_location=current_location,
        active_alert_count=active_alert_count,
        highest_alert_severity=highest_alert_severity,
        active_alerts=[],
    )


def _high_risk_facility():
    return FacilityRiskSummary(
        facility_id=1,
        facility_name="Dallas Mega Cold Storage",
        avg_dwell_hours=7.1,
        detention_risk_band="high",
        visit_count=3,
        confidence="medium",
    )


def test_recommended_decision_returns_best_truck_and_metrics():
    load = _load()
    service = _service(load, [_position("TRUCK-001")])

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert decision.final_recommendation == "RECOMMENDED"
    assert decision.best_truck.truck_id == "TRUCK-001"
    assert decision.best_truck.driver_id == "DRIVER-001"
    assert decision.best_truck.driver_hos_hours_remaining == 8.0
    assert decision.metrics.deadhead_miles == 50
    assert decision.metrics.net_margin == 1735
    assert decision.metrics.stored_costs_used is True
    assert decision.metrics.broker_risk_band == "medium"
    assert decision.best_truck.deadhead_source == DEADHEAD_SOURCE_STORED_FALLBACK
    assert decision.best_truck.can_make_pickup is True
    assert decision.metrics.estimated_revenue_per_hour > 0
    assert decision.metrics.profitability_score > 0
    assert decision.metrics.final_dispatch_score == decision.best_truck.rank_score
    assert decision.best_truck.score_breakdown.facility_multiplier == 1.0
    assert DEMO_SAFE_DEADHEAD_NOTE in decision.decision_notes


def test_avoid_decision_uses_existing_load_evaluation_logic():
    load = _load(revenue=1200, miles=700, deadhead_miles=500)
    service = _service(load, [_position("TRUCK-001")])

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert decision.final_recommendation == "AVOID"
    assert decision.best_truck.recommendation == "AVOID"


def test_review_score_band_maps_to_review():
    load = _load(revenue=1800, miles=700, deadhead_miles=200)
    service = _service(load, [_position("TRUCK-001")])

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert decision.final_recommendation == "REVIEW"
    assert decision.best_truck.recommendation == "REVIEW"


def test_high_facility_risk_applies_multiplier():
    load = _load()
    service = _service(
        load,
        [_position("TRUCK-001")],
        facility_risk=_high_risk_facility(),
    )

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert decision.final_recommendation == "REVIEW"
    assert decision.metrics.expected_dwell_hours == 7.1
    assert decision.best_truck.score_breakdown.facility_multiplier < 1.0
    assert any("High dwell risk" in reason for reason in decision.reasons)


def test_high_broker_risk_applies_multiplier():
    load = _load(broker_name="TQL Risk Desk")
    service = _service(load, [_position("TRUCK-001")])

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert decision.metrics.broker_risk_band == "high"
    assert decision.best_truck.score_breakdown.broker_multiplier < 1.0
    assert "High broker risk from TQL Risk Desk requires dispatcher review" in decision.reasons


def test_ranking_prefers_origin_match_and_penalizes_high_alerts():
    load = _load(truck_id="TRUCK-002")
    positions = [
        _position(
            "TRUCK-001",
            current_location="Dallas yard",
            highest_alert_severity="high",
            active_alert_count=1,
        ),
        _position("TRUCK-002", current_location="Fort Worth staging"),
        _position("TRUCK-003", status="idle", current_location="Dallas terminal"),
    ]
    service = _service(load, positions)

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert [option.truck_id for option in decision.truck_options] == [
        "TRUCK-003",
        "TRUCK-002",
        "TRUCK-001",
    ]
    assert "Available idle truck contributes +4" in decision.truck_options[0].ranking_factors
    assert decision.truck_options[0].score_breakdown.strategy_bonus > 0
    assert decision.truck_options[-1].score_breakdown.alert_penalty == 20


def test_maintenance_trucks_are_excluded():
    load = _load()
    positions = [
        _position("TRUCK-001", status="maintenance"),
        _position("TRUCK-002", status="moving"),
    ]
    service = _service(load, positions)

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert [option.truck_id for option in decision.truck_options] == ["TRUCK-002"]


def test_truck_on_active_load_is_excluded():
    load = _load()
    positions = [
        _position("TRUCK-001", status="idle"),
        _position("TRUCK-002", status="stopped"),
    ]
    service = _service(load, positions, busy_truck_ids={"TRUCK-001"})

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert [option.truck_id for option in decision.truck_options] == ["TRUCK-002"]


def test_per_truck_deadhead_and_pickup_feasibility_hard_filters_infeasible_trucks():
    load = _load(
        revenue=2600,
        miles=780,
        deadhead_miles=400,
        origin="Dallas, TX",
        origin_lat=Decimal("32.776700"),
        origin_lon=Decimal("-96.797000"),
        status="available",
    )
    load.pickup_time = datetime(2026, 6, 1, 16, 0, tzinfo=timezone.utc)
    positions = [
        _position(
            "TRUCK-NEAR",
            status="idle",
            current_location="Dallas yard",
            latitude=32.7767,
            longitude=-96.797,
            last_seen_at=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
        ),
        _position(
            "TRUCK-FAR",
            status="idle",
            current_location="Houston terminal",
            latitude=29.7604,
            longitude=-95.3698,
            last_seen_at=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
        ),
    ]
    service = _service(load, positions)

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert [option.truck_id for option in decision.truck_options] == ["TRUCK-NEAR"]
    near = decision.truck_options[0]
    assert near.deadhead_source == DEADHEAD_SOURCE_HAVERSINE
    assert near.deadhead_miles == 0
    assert near.can_make_pickup is True
    assert decision.metrics.deadhead_miles == 0


def test_driver_on_active_load_and_low_hos_are_excluded():
    load = _load()
    drivers = [
        _driver("DRIVER-BUSY", hos_hours_remaining=Decimal("10.0")),
        _driver("DRIVER-LOW-HOS", hos_hours_remaining=Decimal("1.5")),
        _driver("DRIVER-READY", name="Ready Driver", hos_hours_remaining=Decimal("7.5")),
    ]
    service = _service(
        load,
        [_position("TRUCK-001", status="idle")],
        drivers=drivers,
        busy_driver_ids={"DRIVER-BUSY"},
    )

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert decision.best_truck.driver_id == "DRIVER-READY"
    assert decision.best_truck.driver_name == "Ready Driver"
    assert decision.best_truck.driver_hos_hours_remaining == 7.5


def test_no_available_driver_returns_avoid_without_options():
    load = _load()
    drivers = [
        _driver("DRIVER-LOW-HOS", hos_hours_remaining=Decimal("1.5")),
        _driver("DRIVER-ON-LOAD", status="on_load", hos_hours_remaining=Decimal("9.0")),
    ]
    service = _service(
        load,
        [_position("TRUCK-001", status="idle")],
        drivers=drivers,
    )

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert decision.final_recommendation == "AVOID"
    assert decision.best_truck is None
    assert decision.truck_options == []


def test_no_eligible_trucks_returns_avoid_without_best_truck():
    load = _load()
    service = _service(load, [_position("TRUCK-001", status="maintenance")])

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert decision.final_recommendation == "AVOID"
    assert decision.best_truck is None
    assert decision.truck_options == []
    assert "No eligible trucks" in decision.reasons[0]


def test_load_lookup_is_scoped_to_fleet():
    load = _load(fleet_id=1)
    service = _service(load, [_position("TRUCK-001")])

    decision = service.get_load_decision(db=None, fleet_id=2, load_id=load.load_id)

    assert decision is None


def test_candidate_load_sets_is_candidate_true_and_no_status_note():
    load = _load(status="available")
    service = _service(load, [_position("TRUCK-001")])

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert decision.is_candidate is True
    assert all("not an open dispatch opportunity" not in note for note in decision.decision_notes)


def test_non_candidate_load_sets_is_candidate_false_and_adds_note():
    load = _load(status="booked")
    service = _service(load, [_position("TRUCK-001")])

    decision = service.get_load_decision(db=None, fleet_id=1, load_id=load.load_id)

    assert decision is not None
    assert decision.is_candidate is False
    assert any("not an open dispatch opportunity" in note for note in decision.decision_notes)
    assert any("booked" in note for note in decision.decision_notes)


def test_accept_recommendation_assigns_load_to_truck_and_driver():
    load = _load(status="available", truck_id=None)
    service = _service(load, [_position("TRUCK-001", status="idle")])

    assigned = service.accept_recommendation(
        db=None,
        fleet_id=1,
        load_id=load.load_id,
        truck_id="TRUCK-001",
        driver_id="DRIVER-001",
    )

    assert assigned is not None
    assert assigned.load_id == load.load_id
    assert assigned.truck_id == "TRUCK-001"
    assert assigned.driver_id == "DRIVER-001"
    assert assigned.status == "booked"
    assert load.truck_id == "TRUCK-001"
    assert load.driver_id == "DRIVER-001"
    assert load.status == "booked"


def test_accept_recommendation_rejects_non_candidate_load():
    load = _load(status="booked")
    service = _service(load, [_position("TRUCK-001", status="idle")])

    with pytest.raises(DispatcherAssignmentConflictError, match="already booked"):
        service.accept_recommendation(
            db=None,
            fleet_id=1,
            load_id=load.load_id,
            truck_id="TRUCK-001",
            driver_id="DRIVER-001",
        )


def test_accept_recommendation_rejects_stale_busy_truck():
    load = _load(status="available", truck_id=None)
    service = _service(
        load,
        [_position("TRUCK-001", status="idle")],
        busy_truck_ids={"TRUCK-001"},
    )

    with pytest.raises(DispatcherAssignmentConflictError, match="no longer available"):
        service.accept_recommendation(
            db=None,
            fleet_id=1,
            load_id=load.load_id,
            truck_id="TRUCK-001",
            driver_id="DRIVER-001",
        )


def test_accept_recommendation_rejects_stale_busy_driver():
    load = _load(status="available", truck_id=None)
    service = _service(
        load,
        [_position("TRUCK-001", status="idle")],
        busy_driver_ids={"DRIVER-001"},
    )

    with pytest.raises(DispatcherAssignmentConflictError, match="no longer available"):
        service.accept_recommendation(
            db=None,
            fleet_id=1,
            load_id=load.load_id,
            truck_id="TRUCK-001",
            driver_id="DRIVER-001",
        )


def test_accept_recommendation_is_scoped_to_fleet():
    load = _load(status="available", truck_id=None, fleet_id=1)
    service = _service(load, [_position("TRUCK-001", status="idle")])

    assigned = service.accept_recommendation(
        db=None,
        fleet_id=2,
        load_id=load.load_id,
        truck_id="TRUCK-001",
        driver_id="DRIVER-001",
    )

    assert assigned is None


def test_get_candidate_loads_returns_only_available_loads(seeded_demo_db):
    result = reset_demo_environment(
        seeded_demo_db,
        seed=DEFAULT_DEMO_SEED,
        base_date=DEFAULT_BASE_DATE,
    )
    service = DispatcherCommandCenterService()
    operations_fleet_id = result.fleet_ids["operations"]

    candidates = service.get_candidate_loads(seeded_demo_db, fleet_id=operations_fleet_id)

    candidate_ids = {c.load_id for c in candidates}
    assert candidate_ids == {"DEMO-CAND-GOOD", "DEMO-CAND-WEAK-BROKER", "DEMO-CAND-BAD-DEADHEAD"}
    for candidate in candidates:
        assert candidate.status == "available"
        assert candidate.truck_id is None
        assert candidate.driver_id is None
        assert candidate.equipment_type is not None


def test_seeded_operations_demo_story_has_recommended_review_and_avoid(
    seeded_demo_db,
):
    result = reset_demo_environment(
        seeded_demo_db,
        seed=DEFAULT_DEMO_SEED,
        base_date=DEFAULT_BASE_DATE,
    )
    service = DispatcherCommandCenterService()
    operations_fleet_id = result.fleet_ids["operations"]

    good = service.get_load_decision(
        seeded_demo_db,
        fleet_id=operations_fleet_id,
        load_id="DEMO-CAND-GOOD",
    )
    weak_broker = service.get_load_decision(
        seeded_demo_db,
        fleet_id=operations_fleet_id,
        load_id="DEMO-CAND-WEAK-BROKER",
    )
    bad_deadhead = service.get_load_decision(
        seeded_demo_db,
        fleet_id=operations_fleet_id,
        load_id="DEMO-CAND-BAD-DEADHEAD",
    )

    assert good is not None
    assert good.final_recommendation == "RECOMMENDED"
    assert good.best_truck is not None
    assert good.best_truck.truck_id not in {
        "DEMO-TRUCK-002",
        "DEMO-TRUCK-005",
        "DEMO-TRUCK-006",
    }
    assert good.best_truck.driver_id not in {
        "DEMO-DRIVER-002",
        "DEMO-DRIVER-004",
        "DEMO-DRIVER-005",
    }
    assert good.best_truck.driver_hos_hours_remaining >= 2.0

    assert weak_broker is not None
    assert weak_broker.final_recommendation in {"RECOMMENDED", "REVIEW"}
    assert weak_broker.best_truck.score_breakdown.broker_multiplier < 1.0
    assert weak_broker.best_truck is not None
    assert weak_broker.best_truck.driver_hos_hours_remaining >= 2.0

    assert bad_deadhead is not None
    assert bad_deadhead.final_recommendation == "AVOID"
    assert {"DEMO-TRUCK-002", "DEMO-TRUCK-005", "DEMO-TRUCK-006"}.isdisjoint({
        option.truck_id for option in bad_deadhead.truck_options
    })
