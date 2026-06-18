from app.models.driver import Driver
from app.models.dwell_event import DwellEvent
from app.models.fleet import Fleet
from app.models.load import Load
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.models.facility import Facility, normalize_facility_name
from app.seed.types import (
    DriverSeed,
    DwellEventSeed,
    FacilitySeed,
    FleetSeed,
    LoadSeed,
    TruckSeed,
)
from app.simulator.telemetry import TelemetryEventSeed


def build_fleet(seed: FleetSeed) -> Fleet:
    return Fleet(name=seed.name)


def build_driver(seed: DriverSeed, fleet_id: int) -> Driver:
    return Driver(
        driver_id=seed.driver_id,
        fleet_id=fleet_id,
        name=seed.name,
        status=seed.status,
        hos_hours_remaining=seed.hos_hours_remaining,
    )


def build_truck(seed: TruckSeed, fleet_id: int) -> Truck:
    return Truck(
        truck_id=seed.truck_id,
        fleet_id=fleet_id,
        status=seed.status,
        current_location=seed.current_location,
        current_lat=seed.current_lat,
        current_lon=seed.current_lon,
        last_seen_at=seed.last_seen_at,
    )


def build_load(seed: LoadSeed, fleet_id: int) -> Load:
    return Load(
        load_id=seed.load_id,
        fleet_id=fleet_id,
        truck_id=seed.truck_id,
        driver_id=seed.driver_id,
        equipment_type=seed.equipment_type,
        broker_name=seed.broker_name,
        origin=seed.origin,
        origin_lat=seed.origin_lat,
        origin_lon=seed.origin_lon,
        destination=seed.destination,
        revenue=seed.revenue,
        miles=seed.miles,
        deadhead_miles=seed.deadhead_miles,
        fuel_cost=seed.fuel_cost,
        maintenance_reserve=seed.maintenance_reserve,
        driver_cost=seed.driver_cost,
        tolls=seed.tolls,
        pickup_time=seed.pickup_time,
        delivery_time=seed.delivery_time,
        status=seed.status,
    )


def build_facility(seed: FacilitySeed, fleet_id: int) -> Facility:
    return Facility(
        fleet_id=fleet_id,
        name=seed.name,
        normalized_name=normalize_facility_name(seed.name),
        city=seed.city,
        state=seed.state,
        latitude=seed.latitude,
        longitude=seed.longitude,
        facility_type=seed.facility_type,
    )


def build_dwell_event(
    seed: DwellEventSeed,
    fleet_id: int,
    facility_id: int | None = None,
) -> DwellEvent:
    return DwellEvent(
        load_id=seed.load_id,
        fleet_id=fleet_id,
        facility_id=facility_id,
        facility_name=seed.facility_name,
        broker_name=seed.broker_name,
        appointment_time=seed.appointment_time,
        arrival_time=seed.arrival_time,
        loading_start=seed.loading_start,
        loading_end=seed.loading_end,
        departure_time=seed.departure_time,
        detention_pay=seed.detention_pay,
        driver_notes=seed.driver_notes,
    )


def build_telemetry_event(seed: TelemetryEventSeed, fleet_id: int) -> TelemetryEvent:
    return TelemetryEvent(
        truck_id=seed.truck_id,
        fleet_id=fleet_id,
        timestamp=seed.timestamp,
        gps_lat=seed.latitude,
        gps_lon=seed.longitude,
        speed=seed.speed,
        heading=seed.heading,
        rpm=seed.rpm,
        engine_temp=seed.engine_temp,
        fuel_level=seed.fuel_level,
        idle_minutes=seed.idle_minutes,
        reefer_temp=seed.reefer_temp,
        load_weight=seed.load_weight,
    )

