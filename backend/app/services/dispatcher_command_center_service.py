from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.load import Load
from app.repositories.driver_repository import DriverRepository
from app.repositories.load_repository import CANDIDATE_STATUSES, LoadRepository
from app.schemas.dispatcher_command_center import (
    DispatcherCommandCenterDecision,
    DispatcherDecisionMetrics,
    DispatcherRecommendation,
    DispatcherScoreBreakdown,
    DispatcherTruckOption,
)
from app.schemas.facility import FacilityRiskSummary
from app.schemas.live_position import LiveTruckPosition
from app.schemas.load import LoadResponse
from app.schemas.load_evaluation import LoadEvaluationRequest, LoadEvaluationResponse
from app.services.broker_risk import BrokerRiskBand, broker_risk_for_load
from app.services.deadhead import truck_deadhead_miles
from app.services.facility_service import FacilityService
from app.services.live_position_service import get_live_positions_for_fleet
from app.services.load_evaluation_service import DEFAULT_AVG_SPEED_MPH, clamp, linear_score, evaluate_load


DEMO_SAFE_DEADHEAD_NOTE = (
    "Deadhead uses truck and pickup coordinates when available, with the load's "
    "stored deadhead_miles value as a demo-safe fallback."
)

MAINTENANCE_STATUS = "maintenance"
MIN_DRIVER_HOS_HOURS = Decimal("2.0")


class InvalidLoadEconomicsError(ValueError):
    pass


class DispatcherAssignmentConflictError(ValueError):
    pass


class DispatcherCommandCenterService:
    def __init__(
        self,
        load_repository: LoadRepository | None = None,
        driver_repository: DriverRepository | None = None,
        facility_service: FacilityService | None = None,
        live_positions_provider: Callable[
            [Session, int],
            list[LiveTruckPosition],
        ] = get_live_positions_for_fleet,
    ):
        self.load_repository = load_repository or LoadRepository()
        self.driver_repository = driver_repository or DriverRepository()
        self.facility_service = facility_service or FacilityService()
        self.live_positions_provider = live_positions_provider

    def get_candidate_loads(self, db: Session, fleet_id: int) -> list[LoadResponse]:
        loads = self.load_repository.get_candidate_loads_by_fleet(db, fleet_id)
        facility_risk_by_load = self.facility_service.get_facility_risk_by_load_id(
            db=db,
            fleet_id=fleet_id,
            load_ids=[load.load_id for load in loads],
        )
        results = []
        for load in loads:
            response = LoadResponse.model_validate(load)
            response.facility_risk = facility_risk_by_load.get(load.load_id)
            results.append(response)
        return results

    def get_load_decision(
        self,
        db: Session,
        fleet_id: int,
        load_id: str,
    ) -> DispatcherCommandCenterDecision | None:
        load = self.load_repository.get_by_id_and_fleet(db, load_id, fleet_id)
        if load is None:
            return None

        is_candidate = load.status in CANDIDATE_STATUSES
        facility_risk = self.facility_service.get_facility_risk_by_load_id(
            db=db,
            fleet_id=fleet_id,
            load_ids=[load.load_id],
        ).get(load.load_id)
        broker_risk_band, broker_risk_reason = broker_risk_for_load(load.broker_name)
        truck_options = self._build_truck_options(
            db=db,
            fleet_id=fleet_id,
            load=load,
            facility_risk=facility_risk,
            broker_risk_band=broker_risk_band,
            broker_risk_reason=broker_risk_reason,
        )

        load_response = LoadResponse.model_validate(load)
        load_response.facility_risk = facility_risk

        if truck_options:
            best_truck = truck_options[0]
            evaluation = self._evaluate_load(
                load,
                best_truck.deadhead_miles,
                _expected_dwell_hours(facility_risk),
            )
            final_recommendation = best_truck.recommendation
            reasons = best_truck.reasons
            score_breakdown = best_truck.score_breakdown
        else:
            best_truck = None
            evaluation = self._evaluate_load(load, expected_dwell_hours=_expected_dwell_hours(facility_risk))
            final_recommendation = "AVOID"
            reasons = [
                "No eligible trucks are available for this load",
                broker_risk_reason,
                *_facility_reasoning(facility_risk),
            ]
            score_breakdown = None

        return DispatcherCommandCenterDecision(
            load=load_response,
            best_truck=best_truck,
            truck_options=truck_options,
            facility_risk=facility_risk,
            final_recommendation=final_recommendation,
            metrics=_decision_metrics(
                evaluation,
                load,
                facility_risk,
                broker_risk_band,
                best_truck.deadhead_miles if best_truck else None,
                score_breakdown,
            ),
            reasons=reasons,
            is_candidate=is_candidate,
            decision_notes=_build_decision_notes(load, is_candidate),
        )

    def accept_recommendation(
        self,
        db: Session,
        fleet_id: int,
        load_id: str,
        truck_id: str,
        driver_id: str,
    ) -> LoadResponse | None:
        load = self.load_repository.get_by_id_and_fleet(db, load_id, fleet_id)
        if load is None:
            return None

        if load.status not in CANDIDATE_STATUSES:
            raise DispatcherAssignmentConflictError(
                f"Load {load_id} is already booked or no longer available"
            )

        decision = self.get_load_decision(db=db, fleet_id=fleet_id, load_id=load_id)
        if decision is None:
            return None

        matching_option = next(
            (
                option
                for option in decision.truck_options
                if option.truck_id == truck_id and option.driver_id == driver_id
            ),
            None,
        )
        if matching_option is None:
            raise DispatcherAssignmentConflictError(
                "Requested truck or driver is no longer available for this load"
            )

        assigned_load = self.load_repository.assign(
            db=db,
            load=load,
            truck_id=truck_id,
            driver_id=driver_id,
        )
        return LoadResponse.model_validate(assigned_load)

    def _evaluate_load(
        self,
        load: Load,
        deadhead_miles_override: float | None = None,
        expected_dwell_hours: float = 0.0,
    ) -> LoadEvaluationResponse:
        payout = _positive_decimal(load.revenue, "revenue")
        loaded_miles = _positive_decimal(load.miles, "miles")
        deadhead_miles = (
            Decimal(str(deadhead_miles_override))
            if deadhead_miles_override is not None
            else _non_negative_decimal(load.deadhead_miles, "deadhead_miles")
        )

        return evaluate_load(
            LoadEvaluationRequest(
                payout=float(payout),
                loaded_miles=float(loaded_miles),
                deadhead_miles=float(deadhead_miles),
                equipment_type=getattr(load, "equipment_type", None) or "Unknown",
                fuel_cost=_optional_float(load.fuel_cost),
                maintenance_reserve=_optional_float(load.maintenance_reserve),
                driver_cost=_optional_float(load.driver_cost),
                tolls=_optional_float(load.tolls),
                expected_dwell_hours=expected_dwell_hours,
            )
        )

    def _build_truck_options(
        self,
        db: Session,
        fleet_id: int,
        load: Load,
        facility_risk: FacilityRiskSummary | None,
        broker_risk_band: BrokerRiskBand,
        broker_risk_reason: str,
    ) -> list[DispatcherTruckOption]:
        origin_city = _city_token(load.origin)
        expected_dwell_hours = _expected_dwell_hours(facility_risk)
        positions = self.live_positions_provider(db, fleet_id)
        busy_truck_ids, busy_driver_ids = self.load_repository.get_active_assignments_by_fleet(
            db,
            fleet_id,
        )
        drivers = [
            driver
            for driver in self.driver_repository.get_available_by_fleet(
                db,
                fleet_id,
                MIN_DRIVER_HOS_HOURS,
            )
            if driver.driver_id not in busy_driver_ids
        ]
        driver = _best_driver(drivers)
        if driver is None:
            return []

        options = []

        for position in positions:
            if position.status.lower() == MAINTENANCE_STATUS:
                continue
            if position.truck_id in busy_truck_ids:
                continue

            deadhead_miles, deadhead_source = truck_deadhead_miles(position, load)
            can_make_pickup, eta_hours, hours_until_pickup = _pickup_feasibility(
                position,
                load,
                deadhead_miles,
            )
            if not can_make_pickup:
                continue
            if hours_until_pickup is not None and _driver_hos_insufficient_for_pickup(driver, eta_hours):
                continue

            evaluation = self._evaluate_load(load, deadhead_miles, expected_dwell_hours)
            score_breakdown, ranking_factors = _dispatch_score(
                position=position,
                origin_city=origin_city,
                evaluation=evaluation,
                facility_risk=facility_risk,
                broker_risk_band=broker_risk_band,
            )
            recommendation = _score_to_recommendation(score_breakdown.final_dispatch_score)
            pickup_reasons = _pickup_reasoning(
                can_make_pickup,
                eta_hours,
                hours_until_pickup,
            )
            reasons = [
                *evaluation.reasons,
                *pickup_reasons,
                broker_risk_reason,
                *_facility_reasoning(facility_risk),
                *ranking_factors,
            ]

            options.append(
                DispatcherTruckOption(
                    truck_id=position.truck_id,
                    driver_id=driver.driver_id,
                    driver_name=driver.name,
                    driver_hos_hours_remaining=_driver_hos_hours(driver),
                    status=position.status,
                    current_location=position.current_location,
                    latitude=position.latitude,
                    longitude=position.longitude,
                    last_seen_at=position.last_seen_at,
                    active_alert_count=position.active_alert_count,
                    highest_alert_severity=position.highest_alert_severity,
                    recommendation=recommendation,
                    rank_score=score_breakdown.final_dispatch_score,
                    deadhead_miles=deadhead_miles,
                    deadhead_source=deadhead_source,
                    can_make_pickup=can_make_pickup,
                    estimated_revenue_per_hour=evaluation.metrics.estimated_revenue_per_hour,
                    profitability_score=evaluation.metrics.profitability_score,
                    operational_score=evaluation.metrics.operational_score,
                    score_breakdown=score_breakdown,
                    reasons=reasons,
                    ranking_factors=ranking_factors,
                )
            )

        return sorted(options, key=lambda option: (-option.rank_score, option.truck_id))


def _dispatch_score(
    *,
    position: LiveTruckPosition,
    origin_city: str | None,
    evaluation: LoadEvaluationResponse,
    facility_risk: FacilityRiskSummary | None,
    broker_risk_band: BrokerRiskBand,
) -> tuple[DispatcherScoreBreakdown, list[str]]:
    profitability = evaluation.metrics.profitability_score
    facility_multiplier, facility_factor = _facility_multiplier(facility_risk)
    broker_multiplier, broker_factor = _broker_multiplier(broker_risk_band)
    alert_penalty = _alert_penalty(position)
    strategy_bonus, strategy_factors = _strategy_bonus(position, origin_city)

    final_score = clamp(
        (profitability * facility_multiplier * broker_multiplier)
        - alert_penalty
        + strategy_bonus,
    )

    factors = [
        f"Profitability baseline: {profitability:.0f}/100",
        facility_factor,
        broker_factor,
    ]
    if alert_penalty:
        factors.append(f"Unresolved alert risk applies -{alert_penalty:.0f}")
    else:
        factors.append("No unresolved alert penalty applies")
    factors.extend(strategy_factors)
    factors.append(f"Final dispatch score: {final_score:.0f}/100")

    return (
        DispatcherScoreBreakdown(
            profitability_baseline=round(profitability, 2),
            facility_multiplier=round(facility_multiplier, 2),
            broker_multiplier=round(broker_multiplier, 2),
            alert_penalty=round(alert_penalty, 2),
            strategy_bonus=round(strategy_bonus, 2),
            final_dispatch_score=round(final_score, 2),
        ),
        factors,
    )


def _facility_multiplier(
    facility_risk: FacilityRiskSummary | None,
) -> tuple[float, str]:
    if facility_risk is None:
        return 1.0, "Facility dwell multiplier is 1.00 because facility risk is unavailable"

    dwell_hours = facility_risk.p90_dwell_hours or facility_risk.avg_dwell_hours
    if dwell_hours is not None:
        discount = linear_score(dwell_hours, 2.0, 6.0, minimum_score=0.0, maximum_score=0.25)
        multiplier = 1.0 - discount
        return multiplier, f"Facility dwell multiplier is {multiplier:.2f} from {dwell_hours:.1f}h dwell risk"

    band = (facility_risk.detention_risk_band or "").lower()
    if band == "high":
        return 0.75, "Facility dwell multiplier is 0.75 from high detention risk"
    if band == "medium":
        return 0.90, "Facility dwell multiplier is 0.90 from medium detention risk"
    return 1.0, "Facility dwell multiplier is 1.00 from low or incomplete detention risk"


def _broker_multiplier(broker_risk_band: BrokerRiskBand) -> tuple[float, str]:
    if broker_risk_band == "high":
        return 0.85, "Broker multiplier is 0.85 for high broker risk"
    if broker_risk_band == "medium":
        return 0.95, "Broker multiplier is 0.95 for medium broker risk"
    return 1.0, "Broker multiplier is 1.00 for low broker risk"


def _strategy_bonus(
    position: LiveTruckPosition,
    origin_city: str | None,
) -> tuple[float, list[str]]:
    bonus = 0.0
    factors: list[str] = []

    availability_bonus = _availability_bonus(position.status)
    if availability_bonus:
        bonus += availability_bonus
        factors.append(f"Available {position.status} truck contributes +{availability_bonus:.0f}")

    if _location_matches_origin(position.current_location, origin_city):
        bonus += 8
        factors.append("Current location matches the load origin city +8")

    if not factors:
        factors.append("No strategic bonus applies")

    return bonus, factors


def _score_to_recommendation(score: float) -> DispatcherRecommendation:
    if score >= 80:
        return "RECOMMENDED"
    if score >= 50:
        return "REVIEW"
    return "AVOID"


def _decision_metrics(
    evaluation: LoadEvaluationResponse,
    load: Load,
    facility_risk: FacilityRiskSummary | None,
    broker_risk_band: BrokerRiskBand,
    deadhead_miles: float | None = None,
    score_breakdown: DispatcherScoreBreakdown | None = None,
) -> DispatcherDecisionMetrics:
    return DispatcherDecisionMetrics(
        gross_rpm=evaluation.metrics.gross_rpm,
        deadhead_adjusted_rpm=evaluation.metrics.deadhead_adjusted_rpm,
        estimated_fuel_cost=evaluation.metrics.estimated_fuel_cost,
        estimated_revenue_per_hour=evaluation.metrics.estimated_revenue_per_hour,
        estimated_drive_hours=evaluation.metrics.estimated_drive_hours,
        deadhead_penalty=evaluation.metrics.deadhead_penalty,
        profitability_score=evaluation.metrics.profitability_score,
        operational_score=evaluation.metrics.operational_score,
        net_margin=evaluation.metrics.net_margin,
        stored_costs_used=evaluation.metrics.stored_costs_used,
        broker_risk_band=broker_risk_band,
        deadhead_miles=(
            deadhead_miles
            if deadhead_miles is not None
            else float(_non_negative_decimal(load.deadhead_miles, "deadhead_miles"))
        ),
        expected_dwell_hours=(
            evaluation.metrics.expected_dwell_hours
            if evaluation.metrics.expected_dwell_hours is not None
            else _expected_dwell_hours(facility_risk)
        ),
        facility_detention_risk_band=(
            facility_risk.detention_risk_band if facility_risk else None
        ),
        profitability_baseline=(score_breakdown.profitability_baseline if score_breakdown else None),
        facility_multiplier=(score_breakdown.facility_multiplier if score_breakdown else None),
        broker_multiplier=(score_breakdown.broker_multiplier if score_breakdown else None),
        alert_penalty=(score_breakdown.alert_penalty if score_breakdown else None),
        strategy_bonus=(score_breakdown.strategy_bonus if score_breakdown else None),
        final_dispatch_score=(score_breakdown.final_dispatch_score if score_breakdown else None),
    )


def _expected_dwell_hours(facility_risk: FacilityRiskSummary | None) -> float:
    if facility_risk is None or facility_risk.avg_dwell_hours is None:
        return 0.0
    return max(0.0, float(facility_risk.avg_dwell_hours))


def _positive_decimal(value: object, field_name: str) -> Decimal:
    decimal_value = _decimal(value, field_name)
    if decimal_value <= 0:
        raise InvalidLoadEconomicsError(f"Load {field_name} must be greater than 0")
    return decimal_value


def _non_negative_decimal(value: object, field_name: str) -> Decimal:
    decimal_value = _decimal(value, field_name)
    if decimal_value < 0:
        raise InvalidLoadEconomicsError(f"Load {field_name} cannot be negative")
    return decimal_value


def _decimal(value: object, field_name: str) -> Decimal:
    if value is None:
        raise InvalidLoadEconomicsError(f"Load {field_name} is required")
    return Decimal(str(value))


def _facility_reasoning(facility_risk: FacilityRiskSummary | None) -> list[str]:
    if facility_risk is None:
        return ["No facility dwell risk is available for this load"]

    if facility_risk.detention_risk_band == "high":
        return [
            f"High dwell risk at {facility_risk.facility_name} requires dispatcher review"
        ]
    if facility_risk.detention_risk_band == "medium":
        return [
            f"Medium dwell risk at {facility_risk.facility_name} should be monitored"
        ]
    if facility_risk.detention_risk_band == "low":
        return [f"Low dwell risk at {facility_risk.facility_name} supports the plan"]

    return [f"Facility risk at {facility_risk.facility_name} is incomplete"]


def _availability_bonus(status: str) -> int:
    normalized = status.lower()
    if normalized == "idle":
        return 4
    if normalized == "stopped":
        return 3
    if normalized == "slow":
        return 2
    if normalized == "moving":
        return 1
    return 1


def _pickup_feasibility(
    position: LiveTruckPosition,
    load: Load,
    deadhead_miles: float,
) -> tuple[bool, float | None, float | None]:
    eta_hours = round(deadhead_miles / DEFAULT_AVG_SPEED_MPH, 2)
    if load.pickup_time is None or position.last_seen_at is None:
        return True, eta_hours, None

    pickup_time = _ensure_aware_utc(load.pickup_time)
    last_seen_at = _ensure_aware_utc(position.last_seen_at)
    hours_until_pickup = max(
        0.0,
        (pickup_time - last_seen_at).total_seconds() / 3600,
    )
    return eta_hours <= hours_until_pickup, eta_hours, round(hours_until_pickup, 2)


def _pickup_reasoning(
    can_make_pickup: bool,
    eta_hours: float | None,
    hours_until_pickup: float | None,
) -> list[str]:
    if eta_hours is None or hours_until_pickup is None:
        return ["Pickup timing is incomplete; appointment feasibility did not hard-block this truck"]
    if can_make_pickup:
        return [
            f"Estimated deadhead ETA is {eta_hours:.1f}h with {hours_until_pickup:.1f}h until pickup"
        ]
    return [
        f"Estimated deadhead ETA is {eta_hours:.1f}h, which misses the {hours_until_pickup:.1f}h pickup window"
    ]


def _ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _best_driver(drivers: list[Driver]) -> Driver | None:
    if not drivers:
        return None

    return sorted(
        drivers,
        key=lambda driver: (
            -float(driver.hos_hours_remaining)
            if driver.hos_hours_remaining is not None
            else float("inf"),
            driver.driver_id,
        ),
    )[0]


def _driver_hos_hours(driver: Driver) -> float | None:
    if driver.hos_hours_remaining is None:
        return None
    return float(driver.hos_hours_remaining)


def _driver_hos_insufficient_for_pickup(
    driver: Driver,
    eta_hours: float | None,
) -> bool:
    hos_hours = _driver_hos_hours(driver)
    if hos_hours is None or eta_hours is None:
        return False
    return hos_hours < eta_hours


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _alert_penalty(position: LiveTruckPosition) -> int:
    severity = (position.highest_alert_severity or "").lower()
    if severity == "critical":
        return 30
    if severity == "high":
        return 20
    if severity == "medium":
        return 10
    if severity == "low":
        return 3
    return 0


def _location_matches_origin(location: str | None, origin_city: str | None) -> bool:
    if not location or not origin_city:
        return False
    return origin_city in location.lower()


def _build_decision_notes(load: Load, is_candidate: bool) -> list[str]:
    notes = [DEMO_SAFE_DEADHEAD_NOTE]
    if not is_candidate:
        notes.append(
            f"This load has status '{load.status}' and is not an open dispatch opportunity. "
            "The decision is provided for review only."
        )
    return notes


def _city_token(value: str | None) -> str | None:
    if not value:
        return None
    city = value.split(",", 1)[0].strip().lower()
    return city or None
