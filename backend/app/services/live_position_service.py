from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.repositories.alert_repository import AlertRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.repositories.truck_repository import TruckRepository
from app.schemas.live_position import LivePositionAlert, LiveTruckPosition


SEVERITY_RANK = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def _group_alerts_by_truck_id(alerts: list[Alert]) -> dict[str, list[Alert]]:
    alerts_by_truck_id: dict[str, list[Alert]] = {}

    for alert in alerts:
        alerts_by_truck_id.setdefault(alert.truck_id, []).append(alert)

    return alerts_by_truck_id


def _highest_severity(alerts: list[Alert]) -> str | None:
    if not alerts:
        return None

    return max(
        (alert.severity for alert in alerts),
        key=lambda severity: SEVERITY_RANK.get(severity.lower(), 0),
    )


def _serialize_alerts(alerts: list[Alert]) -> list[LivePositionAlert]:
    return [
        LivePositionAlert(
            id=alert.id,
            severity=alert.severity,
            alert_type=alert.alert_type,
            message=alert.message,
            created_at=alert.created_at,
        )
        for alert in alerts
    ]


def get_live_positions_for_fleet(
    db: Session,
    fleet_id: int,
) -> list[LiveTruckPosition]:
    truck_repository = TruckRepository()
    telemetry_repository = TelemetryRepository()
    alert_repository = AlertRepository()

    trucks = truck_repository.get_all_by_fleet(db, fleet_id)
    latest_events = telemetry_repository.get_latest_positions(db, fleet_id)
    latest_event_by_truck_id = {
        latest_event.truck_id: latest_event for latest_event in latest_events
    }
    alerts_by_truck_id = _group_alerts_by_truck_id(
        alert_repository.get_unresolved_by_fleet(db, fleet_id)
    )

    positions: list[LiveTruckPosition] = []

    for truck in trucks:
        latest_event = latest_event_by_truck_id.get(truck.truck_id)
        active_alerts = alerts_by_truck_id.get(truck.truck_id, [])

        positions.append(
            LiveTruckPosition(
                truck_id=truck.truck_id,
                status=truck.status,
                latitude=float(truck.current_lat)
                if truck.current_lat is not None
                else None,
                longitude=float(truck.current_lon)
                if truck.current_lon is not None
                else None,
                speed=float(latest_event.speed)
                if latest_event and latest_event.speed is not None
                else None,
                heading=latest_event.heading
                if latest_event and latest_event.heading is not None
                else None,
                last_seen_at=truck.last_seen_at,
                current_location=truck.current_location,
                active_alert_count=len(active_alerts),
                highest_alert_severity=_highest_severity(active_alerts),
                active_alerts=_serialize_alerts(active_alerts),
            )
        )

    return positions
