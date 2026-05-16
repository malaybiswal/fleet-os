import argparse
import random
from datetime import datetime, timezone
from app.models.fleet import Fleet

from app.database import SessionLocal
from app.models.alert import Alert
from app.models.driver import Driver
from app.models.dwell_event import DwellEvent
from app.models.load import Load
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from simulator.generators import (
    generate_alerts,
    generate_drivers,
    generate_dwell_events,
    generate_loads,
    generate_telemetry_events,
    generate_trucks,
)

def clear_existing_data(db) -> None:
    db.query(Alert).delete()
    db.query(TelemetryEvent).delete()
    db.query(DwellEvent).delete()
    db.query(Load).delete()
    db.query(Driver).delete()
    db.query(Truck).delete()
    db.query(Fleet).delete()
    db.commit()

def parse_args():
    parser = argparse.ArgumentParser(description="Seed Fleet OS with synthetic data")
    parser.add_argument("--trucks", type=int, default=10)
    parser.add_argument("--drivers", type=int, default=10)
    parser.add_argument("--loads", type=int, default=100)
    parser.add_argument("--dwell-events", type=int, default=200)
    parser.add_argument("--telemetry-events", type=int, default=5000)
    parser.add_argument("--alerts", type=int, default=50)
    parser.add_argument("--start-date", type=str, default="2024-11-01")
    parser.add_argument("--end-date", type=str, default="2024-11-30")
    parser.add_argument("--alert-frequency", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


def parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def clear_existing_data(db) -> None:
    db.query(Alert).delete()
    db.query(TelemetryEvent).delete()
    db.query(DwellEvent).delete()
    db.query(Load).delete()
    db.query(Driver).delete()
    db.query(Truck).delete()
    db.commit()


def seed_database(args) -> None:
    if args.seed is not None:
        random.seed(args.seed)

    start_datetime = parse_date(args.start_date)
    end_datetime = parse_date(args.end_date)

    db = SessionLocal()
    try:
        clear_existing_data(db)

        fleet_alpha = db.query(Fleet).filter(Fleet.name == "Fleet Alpha").first()
        if fleet_alpha is None:
            fleet_alpha = Fleet(name="Fleet Alpha")
            db.add(fleet_alpha)

        fleet_beta = db.query(Fleet).filter(Fleet.name == "Fleet Beta").first()
        if fleet_beta is None:
            fleet_beta = Fleet(name="Fleet Beta")
            db.add(fleet_beta)

        db.commit()

        db.refresh(fleet_alpha)
        db.refresh(fleet_beta)

        fleet_ids = [fleet_alpha.id, fleet_beta.id]

        trucks = generate_trucks(args.trucks)
        drivers = generate_drivers(args.drivers)
        for index, truck in enumerate(trucks):
            truck.fleet_id = fleet_ids[index % len(fleet_ids)]

        db.add_all(trucks)
        db.add_all(drivers)
        db.commit()

        truck_ids = [truck.truck_id for truck in trucks]
        driver_ids = [driver.driver_id for driver in drivers]

        loads = generate_loads(
            count=args.loads,
            truck_ids=truck_ids,
            driver_ids=driver_ids,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        truck_fleet_map = {truck.truck_id: truck.fleet_id for truck in trucks}

        for load in loads:
            load.fleet_id = truck_fleet_map[load.truck_id]
        db.add_all(loads)
        db.commit()

        load_ids = [load.load_id for load in loads]

        dwell_events = generate_dwell_events(
            count=args.dwell_events,
            load_ids=load_ids,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        telemetry_events = generate_telemetry_events(
            count=args.telemetry_events,
            truck_ids=truck_ids,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            alert_frequency=args.alert_frequency,
        )
        alerts = generate_alerts(
            count=args.alerts,
            truck_ids=truck_ids,
        )
        for alert in alerts:
            alert.fleet_id = truck_fleet_map[alert.truck_id]

        db.add_all(dwell_events)
        db.add_all(telemetry_events)
        db.add_all(alerts)
        db.commit()

        print(
            "Seed complete: "
            f"{len(trucks)} trucks, "
            f"{len(drivers)} drivers, "
            f"{len(loads)} loads, "
            f"{len(dwell_events)} dwell events, "
            f"{len(telemetry_events)} telemetry events, "
            f"{len(alerts)} alerts"
        )
    finally:
        db.close()


def main():
    args = parse_args()
    seed_database(args)


if __name__ == "__main__":
    main()