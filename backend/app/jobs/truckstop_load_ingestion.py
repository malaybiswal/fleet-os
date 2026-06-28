import argparse
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from app.config import settings
from app.database import SessionLocal
from app.ingestion.load_ingestion_service import InvalidLoadError, LoadIngestionService
from app.integrations.resilience import CircuitBreaker, RateLimiter, ResilientLoadProvider
from app.integrations.truckstop.client import TruckstopCredentials, build_truckstop_client
from app.integrations.truckstop.mapper import (
    TruckstopMappingError,
    map_truckstop_load_to_normalized,
)
from app.repositories.fleet_integration_repository import FleetIntegrationRepository
from app.repositories.load_repository import LoadRepository
from app.services.integration_service import TRUCKSTOP_PROVIDER, IntegrationService


TRUCKSTOP_SOURCE = "truckstop"


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TruckstopIngestionResult:
    fleets_processed: int
    fetched: int
    ingested: int
    skipped: int


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Truckstop load postings")
    parser.add_argument("--fleet-id", type=int, default=None)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Run one Truckstop ingestion pass")
    mode.add_argument("--poll", action="store_true", help="Poll Truckstop continuously")
    parser.add_argument("--interval-seconds", type=int, default=None)
    parser.add_argument(
        "--purge-source",
        choices=[TRUCKSTOP_SOURCE],
        default=None,
        help="Delete existing loads with this source for each fleet before ingesting",
    )
    return parser.parse_args(argv)


def ingest_truckstop_loads(
    fleet_id: int | None = None,
    *,
    purge_source: str | None = None,
) -> TruckstopIngestionResult:
    db = SessionLocal()
    repository = FleetIntegrationRepository()
    integration_service = IntegrationService(repository)

    try:
        integrations = (
            [
                integration
                for integration in [
                    repository.get_by_fleet_and_provider(
                        db,
                        fleet_id=fleet_id,
                        provider=TRUCKSTOP_PROVIDER,
                    )
                ]
                if integration is not None and integration.status in {"connected", "error"}
            ]
            if fleet_id is not None
            else repository.list_connected_by_provider(db, provider=TRUCKSTOP_PROVIDER)
        )

        totals = TruckstopIngestionResult(
            fleets_processed=0,
            fetched=0,
            ingested=0,
            skipped=0,
        )

        for integration in integrations:
            fleet_result = _ingest_for_integration(
                db,
                integration,
                integration_service,
                repository,
                purge_source=purge_source,
            )
            totals = TruckstopIngestionResult(
                fleets_processed=totals.fleets_processed
                + fleet_result.fleets_processed,
                fetched=totals.fetched + fleet_result.fetched,
                ingested=totals.ingested + fleet_result.ingested,
                skipped=totals.skipped + fleet_result.skipped,
            )

        return totals
    finally:
        db.close()


def _ingest_for_integration(
    db,
    integration,
    integration_service: IntegrationService,
    repository: FleetIntegrationRepository,
    *,
    purge_source: str | None = None,
) -> TruckstopIngestionResult:
    client = None
    fleet_id = integration.fleet_id
    previous_last_sync_at = integration.last_sync_at
    try:
        credentials = TruckstopCredentials.from_dict(
            integration_service.decrypt_truckstop_credentials(integration)
        )
        client = ResilientLoadProvider(
            build_truckstop_client(credentials),
            rate_limiter=RateLimiter(settings.TRUCKSTOP_RATE_LIMIT_PER_MINUTE),
            circuit_breaker=CircuitBreaker(
                failure_threshold=settings.TRUCKSTOP_CIRCUIT_BREAKER_THRESHOLD,
                cooldown_seconds=settings.TRUCKSTOP_CIRCUIT_BREAKER_COOLDOWN_SECONDS,
                provider_name="Truckstop",
            ),
            provider_name="Truckstop",
            max_retries=settings.TRUCKSTOP_MAX_RETRIES,
        )
        client.authenticate()
        payloads = client.search_loads(credentials.filters)

        if purge_source is not None:
            purged = LoadRepository().delete_by_fleet_and_source(
                db,
                fleet_id=fleet_id,
                source=purge_source,
            )
            logger.info(
                "Purged %s existing source=%s loads fleet_id=%s before sync",
                purged,
                purge_source,
                fleet_id,
            )

        service = LoadIngestionService(db)
        ingested = 0
        skipped = 0

        for payload in payloads:
            try:
                normalized = map_truckstop_load_to_normalized(
                    payload,
                    fleet_id=fleet_id,
                )
                service.ingest(normalized)
                ingested += 1
            except (
                TruckstopMappingError,
                InvalidLoadError,
                TypeError,
                ValueError,
            ) as exc:
                logger.warning(
                    "Skipping Truckstop load fleet_id=%s: %s",
                    fleet_id,
                    exc,
                )
                skipped += 1

        repository.update_sync_status(
            db,
            integration=integration,
            status="connected",
            last_sync_at=datetime.now(timezone.utc),
            last_error=None,
        )
        logger.info(
            "Truckstop sync complete fleet_id=%s fetched=%s ingested=%s skipped=%s",
            fleet_id,
            len(payloads),
            ingested,
            skipped,
        )
        return TruckstopIngestionResult(1, len(payloads), ingested, skipped)
    except Exception as exc:
        db.rollback()
        logger.exception("Truckstop sync failed fleet_id=%s", fleet_id)
        repository.update_sync_status(
            db,
            integration=integration,
            status="error",
            last_sync_at=previous_last_sync_at,
            last_error=str(exc),
        )
        return TruckstopIngestionResult(1, 0, 0, 0)
    finally:
        if client is not None:
            client.close()


def poll_truckstop_loads(
    *,
    fleet_id: int | None = None,
    interval_seconds: int | None = None,
    purge_source: str | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    max_iterations: int | None = None,
) -> None:
    interval = interval_seconds or settings.TRUCKSTOP_POLL_INTERVAL_SECONDS
    iteration_count = 0
    while max_iterations is None or iteration_count < max_iterations:
        try:
            result = ingest_truckstop_loads(
                fleet_id=fleet_id,
                purge_source=purge_source,
            )
            logger.info(
                "Truckstop poll complete: fleets=%s fetched=%s ingested=%s skipped=%s",
                result.fleets_processed,
                result.fetched,
                result.ingested,
                result.skipped,
            )
        except Exception:
            logger.exception(
                "Truckstop poll failed; retrying after %s seconds",
                interval,
            )

        iteration_count += 1
        if max_iterations is not None and iteration_count >= max_iterations:
            break
        sleep_fn(interval)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.poll:
        poll_truckstop_loads(
            fleet_id=args.fleet_id,
            interval_seconds=args.interval_seconds,
            purge_source=args.purge_source,
        )
        return 0

    result = ingest_truckstop_loads(
        fleet_id=args.fleet_id,
        purge_source=args.purge_source,
    )
    print(
        "Truckstop sync complete: "
        f"fleets={result.fleets_processed} fetched={result.fetched} "
        f"ingested={result.ingested} skipped={result.skipped}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
