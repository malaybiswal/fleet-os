from app.models.alert import Alert
from app.models.dwell_event import DwellEvent
from app.models.telemetry_event import TelemetryEvent
from app.repositories.alert_repository import AlertRepository


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
        )

        return self.alert_repository.create(db, alert)

    def check_telemetry_alerts(
        self,
        db,
        telemetry_event: TelemetryEvent,
    ) -> list[Alert]:
        created_alerts: list[Alert] = []

        if telemetry_event.fuel_level is not None and telemetry_event.fuel_level < 15:
            alert = self._create_alert_if_not_exists(
                db=db,
                truck_id=telemetry_event.truck_id,
                alert_type="low_fuel",
                severity="medium",
                message=f"Fuel level at {telemetry_event.fuel_level}% for truck {telemetry_event.truck_id}",
            )
            if alert:
                created_alerts.append(alert)

        if telemetry_event.engine_temp is not None and telemetry_event.engine_temp > 230:
            alert = self._create_alert_if_not_exists(
                db=db,
                truck_id=telemetry_event.truck_id,
                alert_type="engine_overheat",
                severity="high",
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
                alert_type="reefer_temp_deviation",
                severity="high",
                message=f"Reefer temperature at {telemetry_event.reefer_temp}°F for truck {telemetry_event.truck_id}",
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
    ) -> Alert | None:
        if dwell_hours <= 4:
            return None

        return self._create_alert_if_not_exists(
            db=db,
            truck_id=truck_id,
            alert_type="high_dwell",
            severity="medium",
            message=f"Dwell time exceeded 4 hours: {dwell_hours:.2f} hours for load {dwell_event.load_id}",
        )