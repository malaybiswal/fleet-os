import argparse
from dataclasses import dataclass

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.alert import Alert
from app.models.driver import Driver
from app.models.dwell_event import DwellEvent
from app.models.load import Load
from app.models.telemetry_event import TelemetryEvent
from app.models.truck import Truck


COUNT_KEYS = (
    "alerts",
    "telemetry_events",
    "dwell_events",
    "loads",
    "drivers",
    "trucks",
)


@dataclass(frozen=True)
class LiveFleetResetResult:
    fleet_id: int
    deleted: dict[str, int]
    dry_run: bool = False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clear local demo live fleet data")
    parser.add_argument("--fleet-id", type=int, default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print rows that would be deleted without writing data",
    )
    return parser.parse_args(argv)


def resolve_live_fleet_id(cli_fleet_id: int | None = None) -> int:
    if cli_fleet_id is not None:
        return cli_fleet_id

    return settings.DEV_FLEET_ID


def count_live_fleet_data(db: Session, fleet_id: int) -> dict[str, int]:
    truck_ids = _truck_ids_for_fleet(db, fleet_id)
    driver_ids = _driver_ids_for_fleet(db, fleet_id)
    load_ids = _load_ids_for_fleet(db, fleet_id, truck_ids, driver_ids)

    return {
        "alerts": db.query(Alert).filter(_alert_filter(fleet_id, truck_ids)).count(),
        "telemetry_events": db.query(TelemetryEvent)
        .filter(_telemetry_filter(fleet_id, truck_ids))
        .count(),
        "dwell_events": db.query(DwellEvent)
        .filter(_dwell_filter(fleet_id, load_ids))
        .count(),
        "loads": db.query(Load)
        .filter(_load_filter(fleet_id, truck_ids, driver_ids))
        .count(),
        "drivers": db.query(Driver).filter(Driver.fleet_id == fleet_id).count(),
        "trucks": db.query(Truck).filter(_truck_filter(fleet_id)).count(),
    }


def reset_live_fleet_data(
    db: Session,
    *,
    fleet_id: int,
    dry_run: bool = False,
) -> LiveFleetResetResult:
    if dry_run:
        return LiveFleetResetResult(
            fleet_id=fleet_id,
            deleted=count_live_fleet_data(db, fleet_id),
            dry_run=True,
        )

    try:
        truck_ids = _truck_ids_for_fleet(db, fleet_id)
        driver_ids = _driver_ids_for_fleet(db, fleet_id)
        load_ids = _load_ids_for_fleet(db, fleet_id, truck_ids, driver_ids)

        deleted = {
            "alerts": db.query(Alert)
            .filter(_alert_filter(fleet_id, truck_ids))
            .delete(synchronize_session=False),
            "telemetry_events": db.query(TelemetryEvent)
            .filter(_telemetry_filter(fleet_id, truck_ids))
            .delete(synchronize_session=False),
            "dwell_events": db.query(DwellEvent)
            .filter(_dwell_filter(fleet_id, load_ids))
            .delete(synchronize_session=False),
            "loads": db.query(Load)
            .filter(_load_filter(fleet_id, truck_ids, driver_ids))
            .delete(synchronize_session=False),
            "drivers": db.query(Driver)
            .filter(Driver.fleet_id == fleet_id)
            .delete(synchronize_session=False),
            "trucks": db.query(Truck)
            .filter(_truck_filter(fleet_id))
            .delete(synchronize_session=False),
        }
        db.commit()
    except Exception:
        db.rollback()
        raise

    return LiveFleetResetResult(
        fleet_id=fleet_id,
        deleted=deleted,
    )


def _truck_ids_for_fleet(db: Session, fleet_id: int) -> list[str]:
    return [
        truck_id
        for (truck_id,) in db.query(Truck.truck_id)
        .filter(_truck_filter(fleet_id))
        .all()
    ]


def _driver_ids_for_fleet(db: Session, fleet_id: int) -> list[str]:
    return [
        driver_id
        for (driver_id,) in db.query(Driver.driver_id)
        .filter(Driver.fleet_id == fleet_id)
        .all()
    ]


def _load_ids_for_fleet(
    db: Session,
    fleet_id: int,
    truck_ids: list[str],
    driver_ids: list[str],
) -> list[str]:
    return [
        load_id
        for (load_id,) in db.query(Load.load_id)
        .filter(_load_filter(fleet_id, truck_ids, driver_ids))
        .all()
    ]


def _alert_filter(fleet_id: int, truck_ids: list[str]):
    return or_(
        Alert.fleet_id == fleet_id,
        Alert.truck_id.in_(truck_ids),
    )


def _telemetry_filter(fleet_id: int, truck_ids: list[str]):
    return or_(
        TelemetryEvent.fleet_id == fleet_id,
        TelemetryEvent.truck_id.in_(truck_ids),
    )


def _dwell_filter(fleet_id: int, load_ids: list[str]):
    return or_(
        DwellEvent.fleet_id == fleet_id,
        DwellEvent.load_id.in_(load_ids),
    )


def _load_filter(
    fleet_id: int,
    truck_ids: list[str],
    driver_ids: list[str],
):
    return or_(
        Load.fleet_id == fleet_id,
        Load.truck_id.in_(truck_ids),
        Load.driver_id.in_(driver_ids),
    )


def _truck_filter(fleet_id: int):
    return or_(
        Truck.fleet_id == fleet_id,
        Truck.truck_id.like("SIM-%"),
        Truck.truck_id.like("GEOTAB-%"),
    )


def reset_live_fleet(
    *,
    fleet_id: int | None = None,
    dry_run: bool = False,
    session_factory=SessionLocal,
) -> LiveFleetResetResult:
    resolved_fleet_id = resolve_live_fleet_id(cli_fleet_id=fleet_id)
    db = session_factory()

    try:
        return reset_live_fleet_data(
            db,
            fleet_id=resolved_fleet_id,
            dry_run=dry_run,
        )
    finally:
        db.close()


def print_result(result: LiveFleetResetResult) -> None:
    prefix = "Live fleet reset dry run complete" if result.dry_run else "Live fleet reset complete"
    delete_label = "Would delete" if result.dry_run else "Deleted"

    print(f"{prefix}: fleet_id={result.fleet_id}")
    print(f"{delete_label}: {_format_counts(result.deleted)}")


def _format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{key}={counts.get(key, 0)}" for key in COUNT_KEYS)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = reset_live_fleet(
        fleet_id=args.fleet_id,
        dry_run=args.dry_run,
    )
    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
