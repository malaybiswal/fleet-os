import math
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.dwell_event import DwellEvent
from app.models.facility import Facility
from app.repositories.facility_repository import FacilityRepository
from app.schemas.facility import FacilityDetail, FacilityIntelligence
from app.services import facility_intelligence as fi

SORT_FIELDS = {
    "operational_score",
    "avg_dwell_hours",
    "detention_risk_score",
    "visit_count",
    "facility_name",
}

APPOINTMENT_GRACE = timedelta(minutes=fi.APPOINTMENT_GRACE_MINUTES)


def _dwell_hours(event: DwellEvent) -> float | None:
    if event.arrival_time and event.departure_time:
        return (event.departure_time - event.arrival_time).total_seconds() / 3600.0
    return None


def _p90(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = math.ceil(0.9 * len(ordered)) - 1
    return ordered[max(0, rank)]


class FacilityService:
    def __init__(self, facility_repository: FacilityRepository | None = None):
        self.facility_repository = facility_repository or FacilityRepository()

    def _build_intelligence(
        self,
        facility: Facility | None,
        legacy_name: str | None,
        events: list[DwellEvent],
    ) -> FacilityIntelligence:
        dwell_values = [hours for event in events if (hours := _dwell_hours(event)) is not None]
        avg_dwell = sum(dwell_values) / len(dwell_values) if dwell_values else None

        appt_visits = 0
        appt_on_time = 0
        delay_hours: list[float] = []
        for event in events:
            if event.appointment_time and event.loading_start:
                appt_visits += 1
                if event.loading_start <= event.appointment_time + APPOINTMENT_GRACE:
                    appt_on_time += 1
                delay = (event.loading_start - event.appointment_time).total_seconds() / 3600.0
                delay_hours.append(max(0.0, delay))

        detention_visits = sum(1 for hours in dwell_values if hours > fi.DETENTION_FREE_HOURS)
        excess_values = [max(0.0, hours - fi.DETENTION_FREE_HOURS) for hours in dwell_values]
        avg_excess = sum(excess_values) / len(excess_values) if excess_values else 0.0

        dwell = fi.dwell_score(avg_dwell) if avg_dwell is not None else None
        reliability = fi.appointment_reliability(appt_visits, appt_on_time)
        risk = fi.detention_risk(len(dwell_values), detention_visits, avg_excess)

        total_detention_pay = sum(
            (Decimal(str(event.detention_pay)) for event in events if event.detention_pay is not None),
            Decimal("0"),
        )
        arrivals = [event.arrival_time for event in events if event.arrival_time]

        return FacilityIntelligence(
            facility_id=facility.id if facility else None,
            facility_name=facility.name if facility else (legacy_name or "Unknown"),
            city=facility.city if facility else None,
            state=facility.state if facility else None,
            latitude=float(facility.latitude) if facility and facility.latitude is not None else None,
            longitude=float(facility.longitude) if facility and facility.longitude is not None else None,
            facility_type=facility.facility_type if facility else None,
            operational_score=fi.operational_score(dwell, reliability, risk),
            dwell_score=dwell,
            avg_dwell_hours=avg_dwell,
            p90_dwell_hours=_p90(dwell_values),
            appointment_reliability_pct=reliability,
            avg_appointment_delay_hours=(
                sum(delay_hours) / len(delay_hours) if delay_hours else None
            ),
            detention_risk_score=risk,
            detention_risk_band=fi.detention_risk_band(risk),
            total_detention_pay=total_detention_pay,
            visit_count=len(events),
            confidence=fi.confidence(len(events)),
            last_visit_at=max(arrivals) if arrivals else None,
        )

    def list_facility_intelligence(
        self,
        db: Session,
        fleet_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        sort: str = "operational_score",
        order: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> list[FacilityIntelligence]:
        rows = self.facility_repository.dwell_rows_for_intelligence(
            db=db,
            fleet_id=fleet_id,
            start_date=start_date,
            end_date=end_date,
        )

        groups: dict[object, tuple[Facility | None, str | None, list[DwellEvent]]] = {}
        for facility, event in rows:
            key = facility.id if facility else f"legacy:{event.facility_name}"
            if key not in groups:
                groups[key] = (facility, event.facility_name, [])
            groups[key][2].append(event)

        results = [
            self._build_intelligence(facility, legacy_name, events)
            for facility, legacy_name, events in groups.values()
        ]

        reverse = order == "desc"

        if sort == "facility_name":
            results.sort(key=lambda item: item.facility_name.lower(), reverse=reverse)
        else:
            results.sort(
                key=lambda item: (
                    getattr(item, sort) is None,
                    getattr(item, sort) if getattr(item, sort) is not None else 0,
                ),
                reverse=reverse,
            )
            if reverse:
                # Keep None entries at the end after a descending sort.
                results.sort(key=lambda item: getattr(item, sort) is None)

        return results[offset : offset + limit]

    def get_facility_detail(
        self,
        db: Session,
        fleet_id: int,
        facility_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        recent_limit: int = 20,
    ) -> FacilityDetail:
        facility = self.facility_repository.get_by_id(db, fleet_id, facility_id)
        if facility is None:
            raise HTTPException(status_code=404, detail="Facility not found")

        rows = self.facility_repository.dwell_rows_for_intelligence(
            db=db,
            fleet_id=fleet_id,
            start_date=start_date,
            end_date=end_date,
            facility_id=facility_id,
        )
        events = [event for _, event in rows]
        intelligence = self._build_intelligence(facility, None, events)
        return FacilityDetail(
            **intelligence.model_dump(),
            recent_dwell_events=events[:recent_limit],
        )
