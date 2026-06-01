import argparse
import logging
import time
from typing import Callable

from app.config import settings
from app.database import SessionLocal
from app.ingestion.telemetry_ingestion_service import TelemetryIngestionService
from app.integrations.simulator.client import fetch_simulated_vehicle_payloads
from app.integrations.simulator.mapper import map_simulator_payload_to_event


logger = logging.getLogger(__name__)
DEFAULT_SIMULATOR_POLL_INTERVAL_SECONDS = 10


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


def resolve_simulator_fleet_id(cli_fleet_id: int | None = None) -> int:
    if cli_fleet_id is not None:
        return cli_fleet_id

    return settings.DEV_FLEET_ID


def ingest_simulated_telemetry(fleet_id: int | None = None) -> int:
    resolved_fleet_id = resolve_simulator_fleet_id(cli_fleet_id=fleet_id)
    db = SessionLocal()

    try:
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
