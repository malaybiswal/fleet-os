from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SimulatorConfig:
    trucks: int = 10
    drivers: int = 10
    loads: int = 100
    dwell_events: int = 200
    telemetry_events: int = 5000
    alerts: int = 50
    start_date: date = date(2024, 11, 1)
    end_date: date = date(2024, 11, 30)
    alert_frequency: float = 0.1
    seed: int | None = None