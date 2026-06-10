import argparse
import logging
import time
from typing import Callable

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.ingestion.telemetry_ingestion_service import TelemetryIngestionService
from app.integrations.simulator.client import fetch_simulated_vehicle_payloads
from app.integrations.simulator.mapper import map_simulator_payload_to_event
from app.models.fleet import Fleet
from app.seed.mock_fleets import DEMO_FLEET_NAMES


logger = logging.getLogger(__name__)
DEFAULT_SIMULATOR_POLL_INTERVAL_SECONDS = 10
DEFAULT_SIMULATOR_DEMO_FLEET_NAME = DEMO_FLEET_NAMES[0]


class SimulatorFleetResolutionError(RuntimeError):
    pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest simulated telemetry")
    parser.add_argument("--fleet-id", type=int, default=None)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Run one ingestion pass")
    mode.add_argument("--poll", action="store_true", help="Poll simulator continuously")
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=None,
        help="Polling interval in seconds when --poll is enabled",
    )
    return parser.parse_args(argv)


def resolve_simulator_fleet_id(
    cli_fleet_id: int | None = None,
    db: Session | None = None,
) -> int:
    if cli_fleet_id is not None:
        return cli_fleet_id

    owns_session = db is None
    db = db or SessionLocal()

    try:
        return _get_or_create_demo_fleet_id(db)
    finally:
        if owns_session:
            db.close()


def _get_or_create_demo_fleet_id(db: Session) -> int:
    try:
        fleet = _find_demo_fleet(db)
        if fleet is not None:
            return fleet.id

        fleet = Fleet(name=DEFAULT_SIMULATOR_DEMO_FLEET_NAME)
        db.add(fleet)
        db.commit()
        db.refresh(fleet)
        return fleet.id
    except IntegrityError as exc:
        db.rollback()
        try:
            fleet = _find_demo_fleet(db)
            if fleet is not None:
                return fleet.id
        except SQLAlchemyError:
            pass

        raise SimulatorFleetResolutionError(
            "Unable to create simulator demo fleet "
            f"{DEFAULT_SIMULATOR_DEMO_FLEET_NAME!r}; supply --fleet-id explicitly."
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise SimulatorFleetResolutionError(
            "Unable to resolve simulator demo fleet from the database; "
            "supply --fleet-id explicitly or fix database access."
        ) from exc


def _find_demo_fleet(db: Session) -> Fleet | None:
    for fleet_name in DEMO_FLEET_NAMES:
        fleet = db.query(Fleet).filter(Fleet.name == fleet_name).one_or_none()
        if fleet is not None:
            return fleet

    return None


def ingest_simulated_telemetry(fleet_id: int | None = None) -> int:
    db = SessionLocal()

    try:
        resolved_fleet_id = resolve_simulator_fleet_id(
            cli_fleet_id=fleet_id,
            db=db,
        )
        service = TelemetryIngestionService(db, auto_create_trucks=True)
        payloads = fetch_simulated_vehicle_payloads()

        ingested_count = 0

        for payload in payloads:
            payload["fleet_id"] = resolved_fleet_id
            event = map_simulator_payload_to_event(payload)
            service.ingest(event)
            ingested_count += 1

        return ingested_count
    finally:
        db.close()


def poll_simulated_telemetry(
    *,
    fleet_id: int | None = None,
    interval_seconds: int | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    max_iterations: int | None = None,
) -> None:
    interval = interval_seconds or DEFAULT_SIMULATOR_POLL_INTERVAL_SECONDS
    iteration_count = 0

    while max_iterations is None or iteration_count < max_iterations:
        try:
            count = ingest_simulated_telemetry(fleet_id=fleet_id)
            logger.info("Simulator poll complete: ingested=%s", count)
        except Exception:
            logger.exception(
                "Simulator poll failed; retrying after %s seconds",
                interval,
            )

        iteration_count += 1

        if max_iterations is not None and iteration_count >= max_iterations:
            break

        sleep_fn(interval)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    interval_seconds = args.interval_seconds or DEFAULT_SIMULATOR_POLL_INTERVAL_SECONDS

    if args.poll:
        poll_simulated_telemetry(
            fleet_id=args.fleet_id,
            interval_seconds=interval_seconds,
        )
        return 0

    count = ingest_simulated_telemetry(fleet_id=args.fleet_id)
    print(f"Ingested {count} simulated telemetry events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
