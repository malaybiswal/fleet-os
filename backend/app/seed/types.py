from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.simulator.telemetry import TelemetryEventSeed


@dataclass(frozen=True)
class FleetSeed:
    key: str
    name: str


@dataclass(frozen=True)
class DriverSeed:
    driver_id: str
    fleet_key: str
    name: str
    status: str


@dataclass(frozen=True)
class TruckSeed:
    truck_id: str
    fleet_key: str
    status: str
    current_location: str
    current_lat: Decimal
    current_lon: Decimal
    last_seen_at: datetime


@dataclass(frozen=True)
class LoadSeed:
    load_id: str
    fleet_key: str
    truck_id: str
    driver_id: str
    scenario_key: str
    broker_name: str
    origin: str
    destination: str
    revenue: Decimal
    miles: Decimal
    deadhead_miles: Decimal
    fuel_cost: Decimal
    maintenance_reserve: Decimal
    driver_cost: Decimal
    tolls: Decimal
    pickup_time: datetime
    delivery_time: datetime
    status: str


@dataclass(frozen=True)
class DwellEventSeed:
    load_id: str
    fleet_key: str
    facility_name: str
    broker_name: str
    appointment_time: datetime
    arrival_time: datetime
    loading_start: datetime
    loading_end: datetime
    departure_time: datetime
    detention_pay: Decimal
    driver_notes: str


@dataclass(frozen=True)
class AlertSeed:
    truck_id: str
    fleet_key: str
    severity: str
    alert_type: str
    message: str
    created_at: datetime
    resolved: bool


@dataclass(frozen=True)
class DemoSeedDataset:
    seed: int
    base_date: datetime
    fleets: tuple[FleetSeed, ...]
    drivers: tuple[DriverSeed, ...]
    trucks: tuple[TruckSeed, ...]
    loads: tuple[LoadSeed, ...]
    dwell_events: tuple[DwellEventSeed, ...]
    telemetry_events: tuple[TelemetryEventSeed, ...]
    alerts: tuple[AlertSeed, ...]

    def counts(self) -> dict[str, int]:
        return {
            "fleets": len(self.fleets),
            "trucks": len(self.trucks),
            "drivers": len(self.drivers),
            "loads": len(self.loads),
            "dwell_events": len(self.dwell_events),
            "telemetry_events": len(self.telemetry_events),
            "alerts": len(self.alerts),
        }
