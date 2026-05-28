from dataclasses import dataclass

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.driver import Driver
from app.models.dwell_event import DwellEvent
from app.models.fleet import Fleet
from app.models.load import Load
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck
from app.models.user import User
from app.seed.demo_dataset import build_demo_dataset
from app.seed.mock_fleets import (
    DEMO_FLEET_NAMES,
    DEMO_ID_PREFIX,
    DEFAULT_BASE_DATE,
    DEFAULT_DEMO_SEED,
)
from app.seed.types import DemoSeedDataset
from app.seed.generators import (
    build_alert,
    build_driver,
    build_dwell_event,
    build_fleet,
    build_load,
    build_telemetry_event,
    build_truck,
)


@dataclass(frozen=True)
class SeedResult:
    deleted: dict[str, int]
    created: dict[str, int]
    fleet_ids: dict[str, int]
    fleet_names: tuple[str, ...]
    dry_run: bool = False


def reset_demo_environment(
    db: Session,
    seed: int = DEFAULT_DEMO_SEED,
    base_date=DEFAULT_BASE_DATE,
) -> SeedResult:
    dataset = build_demo_dataset(seed=seed, base_date=base_date)
    deleted = delete_demo_data(db)
    fleet_ids = persist_demo_dataset(db, dataset)

    return SeedResult(
        deleted=deleted,
        created=dataset.counts(),
        fleet_ids=fleet_ids,
        fleet_names=tuple(fleet.name for fleet in dataset.fleets),
    )


def dry_run_demo_environment(
    db: Session,
    seed: int = DEFAULT_DEMO_SEED,
    base_date=DEFAULT_BASE_DATE,
) -> SeedResult:
    dataset = build_demo_dataset(seed=seed, base_date=base_date)
    return SeedResult(
        deleted=count_demo_data_to_delete(db),
        created=dataset.counts(),
        fleet_ids={},
        fleet_names=tuple(fleet.name for fleet in dataset.fleets),
        dry_run=True,
    )


def persist_demo_dataset(
    db: Session,
    dataset: DemoSeedDataset,
) -> dict[str, int]:
    fleet_ids: dict[str, int] = {}

    try:
        for fleet_seed in dataset.fleets:
            fleet = (
                db.query(Fleet)
                .filter(Fleet.name == fleet_seed.name)
                .one_or_none()
            )
            if fleet is None:
                fleet = build_fleet(fleet_seed)
                db.add(fleet)
                db.flush()
            fleet_ids[fleet_seed.key] = fleet.id

        db.add_all(
            build_truck(truck_seed, fleet_ids[truck_seed.fleet_key])
            for truck_seed in dataset.trucks
        )
        db.add_all(
            build_driver(driver_seed, fleet_ids[driver_seed.fleet_key])
            for driver_seed in dataset.drivers
        )
        db.flush()

        db.add_all(
            build_load(load_seed, fleet_ids[load_seed.fleet_key])
            for load_seed in dataset.loads
        )
        db.flush()

        db.add_all(
            build_dwell_event(dwell_seed, fleet_ids[dwell_seed.fleet_key])
            for dwell_seed in dataset.dwell_events
        )
        db.add_all(
            build_telemetry_event(telemetry_seed, fleet_ids[telemetry_seed.fleet_key])
            for telemetry_seed in dataset.telemetry_events
        )
        db.add_all(
            build_alert(alert_seed, fleet_ids[alert_seed.fleet_key])
            for alert_seed in dataset.alerts
        )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return fleet_ids


def delete_demo_data(db: Session) -> dict[str, int]:
    demo_fleet_ids = _demo_fleet_ids(db)
    demo_truck_ids = _demo_truck_ids(db, demo_fleet_ids)
    demo_driver_ids = _demo_driver_ids(db, demo_fleet_ids)
    demo_load_ids = _demo_load_ids(db, demo_fleet_ids)

    deleted = {
        "alerts": _delete_alerts(db, demo_fleet_ids, demo_truck_ids),
        "telemetry_events": _delete_telemetry_events(db, demo_fleet_ids, demo_truck_ids),
        "dwell_events": _delete_dwell_events(db, demo_fleet_ids, demo_load_ids),
        "loads": _delete_loads(db, demo_fleet_ids, demo_load_ids),
        "drivers": _delete_drivers(db, demo_fleet_ids, demo_driver_ids),
        "trucks": _delete_trucks(db, demo_fleet_ids, demo_truck_ids),
        "fleets": _delete_unreferenced_fleets(db),
    }
    db.commit()

    return deleted


def count_demo_data(db: Session) -> dict[str, int]:
    demo_fleet_ids = _demo_fleet_ids(db)
    demo_truck_ids = _demo_truck_ids(db, demo_fleet_ids)
    demo_driver_ids = _demo_driver_ids(db, demo_fleet_ids)
    demo_load_ids = _demo_load_ids(db, demo_fleet_ids)

    return {
        "fleets": db.query(Fleet).filter(Fleet.name.in_(DEMO_FLEET_NAMES)).count(),
        "trucks": db.query(Truck).filter(_truck_filter(demo_fleet_ids, demo_truck_ids)).count(),
        "drivers": db.query(Driver).filter(_driver_filter(demo_fleet_ids, demo_driver_ids)).count(),
        "loads": db.query(Load).filter(_load_filter(demo_fleet_ids, demo_load_ids)).count(),
        "dwell_events": db.query(DwellEvent).filter(_dwell_filter(demo_fleet_ids, demo_load_ids)).count(),
        "telemetry_events": db.query(TelemetryEvent).filter(_telemetry_filter(demo_fleet_ids, demo_truck_ids)).count(),
        "alerts": db.query(Alert).filter(_alert_filter(demo_fleet_ids, demo_truck_ids)).count(),
    }


def count_demo_data_to_delete(db: Session) -> dict[str, int]:
    counts = count_demo_data(db)
    counts["fleets"] = _count_unreferenced_fleets(db)
    return counts


def _demo_fleet_ids(db: Session) -> list[int]:
    return [
        fleet_id
        for (fleet_id,) in db.query(Fleet.id)
        .filter(Fleet.name.in_(DEMO_FLEET_NAMES))
        .all()
    ]


def _demo_truck_ids(db: Session, demo_fleet_ids: list[int]) -> list[str]:
    return [
        truck_id
        for (truck_id,) in db.query(Truck.truck_id)
        .filter(_truck_filter(demo_fleet_ids, []))
        .all()
    ]


def _demo_driver_ids(db: Session, demo_fleet_ids: list[int]) -> list[str]:
    return [
        driver_id
        for (driver_id,) in db.query(Driver.driver_id)
        .filter(_driver_filter(demo_fleet_ids, []))
        .all()
    ]


def _demo_load_ids(db: Session, demo_fleet_ids: list[int]) -> list[str]:
    return [
        load_id
        for (load_id,) in db.query(Load.load_id)
        .filter(_load_filter(demo_fleet_ids, []))
        .all()
    ]


def _delete_alerts(
    db: Session,
    demo_fleet_ids: list[int],
    demo_truck_ids: list[str],
) -> int:
    return db.query(Alert).filter(_alert_filter(demo_fleet_ids, demo_truck_ids)).delete(synchronize_session=False)


def _delete_telemetry_events(
    db: Session,
    demo_fleet_ids: list[int],
    demo_truck_ids: list[str],
) -> int:
    return db.query(TelemetryEvent).filter(_telemetry_filter(demo_fleet_ids, demo_truck_ids)).delete(synchronize_session=False)


def _delete_dwell_events(
    db: Session,
    demo_fleet_ids: list[int],
    demo_load_ids: list[str],
) -> int:
    return db.query(DwellEvent).filter(_dwell_filter(demo_fleet_ids, demo_load_ids)).delete(synchronize_session=False)


def _delete_loads(
    db: Session,
    demo_fleet_ids: list[int],
    demo_load_ids: list[str],
) -> int:
    return db.query(Load).filter(_load_filter(demo_fleet_ids, demo_load_ids)).delete(synchronize_session=False)


def _delete_drivers(
    db: Session,
    demo_fleet_ids: list[int],
    demo_driver_ids: list[str],
) -> int:
    return db.query(Driver).filter(_driver_filter(demo_fleet_ids, demo_driver_ids)).delete(synchronize_session=False)


def _delete_trucks(
    db: Session,
    demo_fleet_ids: list[int],
    demo_truck_ids: list[str],
) -> int:
    return db.query(Truck).filter(_truck_filter(demo_fleet_ids, demo_truck_ids)).delete(synchronize_session=False)


def _delete_unreferenced_fleets(db: Session) -> int:
    query = _unreferenced_demo_fleets_query(db)
    return query.delete(synchronize_session=False)


def _count_unreferenced_fleets(db: Session) -> int:
    return _unreferenced_demo_fleets_query(db).count()


def _unreferenced_demo_fleets_query(db: Session):
    referenced_demo_fleet_ids = [
        fleet_id
        for (fleet_id,) in db.query(User.fleet_id)
        .join(Fleet, User.fleet_id == Fleet.id)
        .filter(Fleet.name.in_(DEMO_FLEET_NAMES))
        .distinct()
        .all()
    ]

    query = db.query(Fleet).filter(Fleet.name.in_(DEMO_FLEET_NAMES))
    if referenced_demo_fleet_ids:
        query = query.filter(Fleet.id.notin_(referenced_demo_fleet_ids))

    return query


def _alert_filter(demo_fleet_ids: list[int], demo_truck_ids: list[str]):
    return or_(
        Alert.fleet_id.in_(demo_fleet_ids),
        Alert.truck_id.in_(demo_truck_ids),
        Alert.truck_id.like(f"{DEMO_ID_PREFIX}%"),
    )


def _telemetry_filter(demo_fleet_ids: list[int], demo_truck_ids: list[str]):
    return or_(
        TelemetryEvent.fleet_id.in_(demo_fleet_ids),
        TelemetryEvent.truck_id.in_(demo_truck_ids),
        TelemetryEvent.truck_id.like(f"{DEMO_ID_PREFIX}%"),
    )


def _dwell_filter(demo_fleet_ids: list[int], demo_load_ids: list[str]):
    return or_(
        DwellEvent.fleet_id.in_(demo_fleet_ids),
        DwellEvent.load_id.in_(demo_load_ids),
        DwellEvent.load_id.like(f"{DEMO_ID_PREFIX}%"),
    )


def _load_filter(demo_fleet_ids: list[int], demo_load_ids: list[str]):
    return or_(
        Load.fleet_id.in_(demo_fleet_ids),
        Load.load_id.in_(demo_load_ids),
        Load.load_id.like(f"{DEMO_ID_PREFIX}%"),
    )


def _driver_filter(demo_fleet_ids: list[int], demo_driver_ids: list[str]):
    return or_(
        Driver.fleet_id.in_(demo_fleet_ids),
        Driver.driver_id.in_(demo_driver_ids),
        Driver.driver_id.like(f"{DEMO_ID_PREFIX}%"),
    )


def _truck_filter(demo_fleet_ids: list[int], demo_truck_ids: list[str]):
    return or_(
        Truck.fleet_id.in_(demo_fleet_ids),
        Truck.truck_id.in_(demo_truck_ids),
        Truck.truck_id.like(f"{DEMO_ID_PREFIX}%"),
    )
