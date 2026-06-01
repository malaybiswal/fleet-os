import argparse
import logging
import time
from dataclasses import dataclass
from typing import Callable

from app.config import settings
from app.database import SessionLocal
from app.ingestion.telemetry_ingestion_service import TelemetryIngestionService
from app.integrations.geotab.client import build_geotab_client
from app.integrations.geotab.mapper import (
    GeotabMappingError,
    map_device_status_info_to_event,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeotabIngestionResult:
    fetched: int
    ingested: int
    skipped: int


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Geotab telemetry")
    parser.add_argument("--fleet-id", type=int, default=None)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Run one ingestion pass")
    mode.add_argument("--poll", action="store_true", help="Poll Geotab continuously")
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=None,
        help="Polling interval in seconds when --poll is enabled",
    )
    return parser.parse_args(argv)


def resolve_geotab_fleet_id(
    cli_fleet_id: int | None = None,
) -> int:
    if cli_fleet_id is not None:
        return cli_fleet_id

    return settings.DEV_FLEET_ID


def resolve_fleet_id(fleet_id: int | None = None) -> int:
    return resolve_geotab_fleet_id(cli_fleet_id=fleet_id)


def ingest_geotab_telemetry(fleet_id: int | None = None) -> int:
    return ingest_geotab_telemetry_with_result(fleet_id=fleet_id).ingested


def ingest_geotab_telemetry_with_result(
    fleet_id: int | None = None,
) -> GeotabIngestionResult:
    resolved_fleet_id = resolve_geotab_fleet_id(cli_fleet_id=fleet_id)
    client = build_geotab_client(
        database=settings.GEOTAB_DATABASE,
        username=settings.GEOTAB_USERNAME,
        password=settings.GEOTAB_PASSWORD,
    )
    db = SessionLocal()

    try:
        service = TelemetryIngestionService(db, auto_create_trucks=True)
        payloads = client.fetch_device_status_info()
        ingested_count = 0
        skipped_count = 0

        for payload in payloads:
            try:
                event = map_device_status_info_to_event(
                    payload,
                    fleet_id=resolved_fleet_id,
                )
            except (GeotabMappingError, TypeError, ValueError) as exc:
                logger.warning("Skipping malformed Geotab DeviceStatusInfo: %s", exc)
                skipped_count += 1
                continue

            service.ingest(event)
            ingested_count += 1

        return GeotabIngestionResult(
            fetched=len(payloads),
            ingested=ingested_count,
            skipped=skipped_count,
        )
    finally:
        client.close()
        db.close()


def poll_geotab_telemetry(
    *,
    fleet_id: int | None = None,
    interval_seconds: int | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    max_iterations: int | None = None,
) -> None:
    interval = interval_seconds or settings.GEOTAB_POLL_INTERVAL_SECONDS
    iteration_count = 0

    while max_iterations is None or iteration_count < max_iterations:
        try:
            result = ingest_geotab_telemetry_with_result(fleet_id=fleet_id)
            logger.info(
                "Geotab poll complete: fetched=%s ingested=%s skipped=%s",
                result.fetched,
                result.ingested,
                result.skipped,
            )
        except Exception:
            logger.exception("Geotab poll failed; retrying after %s seconds", interval)

        iteration_count += 1

        if max_iterations is not None and iteration_count >= max_iterations:
            break

        sleep_fn(interval)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    interval_seconds = args.interval_seconds or settings.GEOTAB_POLL_INTERVAL_SECONDS

    if args.poll:
        poll_geotab_telemetry(
            fleet_id=args.fleet_id,
            interval_seconds=interval_seconds,
        )
        return 0

    count = ingest_geotab_telemetry(fleet_id=args.fleet_id)
    print(f"Ingested {count} Geotab telemetry events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
