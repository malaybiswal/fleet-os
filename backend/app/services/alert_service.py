from enum import StrEnum

from app.models.alert import Alert
from app.models.dwell_event import DwellEvent
from app.models.telemetry_event import TelemetryEvent
from app.repositories.alert_repository import AlertRepository

SPEEDING_THRESHOLD_MPH = 65


class AlertType(StrEnum):
    LOW_FUEL = "low_fuel"
    ENGINE_OVERHEAT = "engine_overheat"
    REEFER_TEMP_DEVIATION = "reefer_temp_deviation"
    HIGH_DWELL = "high_dwell"
    SPEEDING = "speeding"        # rule added in TASK-034B
    MAINTENANCE = "maintenance"  # rule added in TASK-034C
    IDLE_TOO_LONG = "idle_too_long"  # rule added in TASK-034D


class AlertService:
    def __init__(self, alert_repository: AlertRepository | None = None):
        self.alert_repository = alert_repository or AlertRepository()

    def _create_alert_if_not_exists(
        self,
        db,
        truck_id: str,
        alert_type: str,
        severity: str,
        message: str,
        fleet_id: int,
    ) -> Alert | None:
        exists = self.alert_repository.exists_unresolved(
            db=db,
            truck_id=truck_id,
            alert_type=alert_type,
        )

        if exists:
            return None

        alert = Alert(
            truck_id=truck_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            resolved=False,
            fleet_id=fleet_id,
        )

        return self.alert_repository.create(db, alert)

    def check_telemetry_alerts(
        self,
        db,
        fleet_id: int,
        telemetry_event: TelemetryEvent,
    ) -> list[Alert]:
        created_alerts: list[Alert] = []

        if telemetry_event.fuel_level is not None and telemetry_event.fuel_level < 15:
            alert = self._create_alert_if_not_exists(
                db=db,
                fleet_id=fleet_id,
                truck_id=telemetry_event.truck_id,
                alert_type=AlertType.LOW_FUEL,
                severity="medium",
                message=f"Fuel level at {telemetry_event.fuel_level}% for truck {telemetry_event.truck_id}",
            )
            if alert:
                created_alerts.append(alert)

        if telemetry_event.engine_temp is not None and telemetry_event.engine_temp > 230:
            alert = self._create_alert_if_not_exists(
                db=db,
                truck_id=telemetry_event.truck_id,
                alert_type=AlertType.ENGINE_OVERHEAT,
                severity="high",
                fleet_id=fleet_id,
                message=f"Engine temperature at {telemetry_event.engine_temp}°F for truck {telemetry_event.truck_id}",
            )
            if alert:
                created_alerts.append(alert)

        if telemetry_event.reefer_temp is not None and (
            telemetry_event.reefer_temp < 34 or telemetry_event.reefer_temp > 38
        ):
            alert = self._create_alert_if_not_exists(
                db=db,
                truck_id=telemetry_event.truck_id,
                alert_type=AlertType.REEFER_TEMP_DEVIATION,
                severity="high",
                fleet_id=fleet_id,
                message=f"Reefer temperature at {telemetry_event.reefer_temp}°F for truck {telemetry_event.truck_id}",
            )
            if alert:
                created_alerts.append(alert)

        if telemetry_event.speed is not None and telemetry_event.speed > SPEEDING_THRESHOLD_MPH:
            alert = self._create_alert_if_not_exists(
                db=db,
                fleet_id=fleet_id,
                truck_id=telemetry_event.truck_id,
                alert_type=AlertType.SPEEDING,
                severity="high",
                message=f"Truck {telemetry_event.truck_id} recorded {telemetry_event.speed} mph, exceeding {SPEEDING_THRESHOLD_MPH} mph limit",
            )
            if alert:
                created_alerts.append(alert)

        return created_alerts

    def check_dwell_alert(
        self,
        db,
        dwell_event: DwellEvent,
        dwell_hours: float,
        truck_id: str,
        fleet_id: int,
    ) -> Alert | None:
        if dwell_hours <= 4:
            return None

        return self._create_alert_if_not_exists(
            db=db,
            truck_id=truck_id,
            alert_type=AlertType.HIGH_DWELL,
            severity="medium",
            message=f"Dwell time exceeded 4 hours: {dwell_hours:.2f} hours for load {dwell_event.load_id}",
            fleet_id=fleet_id,
        )

    def check_status_alerts(
        self,
        db,
        fleet_id: int,
        truck_id: str,
        operational_status: str,
    ) -> list[Alert]:
        """Evaluate operational-status-based alert rules. Rules added in TASK-034C/034D."""
        return []

    def evaluate_telemetry_alerts(
        self,
        db,
        fleet_id: int,
        telemetry_event: TelemetryEvent,
        operational_status: str,
    ) -> list[Alert]:
        """Single entry point for all telemetry-driven alert evaluation.

        Both the ingestion worker (TelemetryIngestionService) and the API layer
        (TelemetryService) call this method so alert logic is never duplicated at
        the call site. Rule implementations live in check_telemetry_alerts() and
        check_status_alerts() and are extended by TASK-034B/C/D.
        """
        alerts = self.check_telemetry_alerts(db=db, fleet_id=fleet_id, telemetry_event=telemetry_event)
        alerts += self.check_status_alerts(db=db, fleet_id=fleet_id, truck_id=telemetry_event.truck_id, operational_status=operational_status)
        return alerts