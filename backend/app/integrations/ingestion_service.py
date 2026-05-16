import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.integrations.base import BaseProvider
from app.repositories.driver_repository import DriverRepository
from app.repositories.ingestion_run_repository import IngestionRunRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.repositories.truck_repository import TruckRepository
from app.schemas.ingestion_run import IngestionRunCreate, IngestionRunUpdate

logger = logging.getLogger("fleet_os.ingestion")

_DEFAULT_LOOKBACK_HOURS = 24


class IngestionService:
    """
    Provider-agnostic orchestrator.  Knows nothing about Motive, Samsara, or
    any other provider — it talks only to BaseProvider and the repositories.
    """

    def __init__(self) -> None:
        self._run_repo = IngestionRunRepository()
        self._truck_repo = TruckRepository()
        self._driver_repo = DriverRepository()
        self._telemetry_repo = TelemetryRepository()

    async def sync_entity(
        self, db: Session, provider: BaseProvider, entity_type: str
    ) -> None:
        """
        Fetch one entity type from `provider`, normalize it, and upsert into the DB.
        entity_type must be one of: "truck", "driver", "telemetry".
        """
        since = self._get_cursor(db, provider.provider_name, entity_type)
        now = datetime.now(timezone.utc)

        run = self._run_repo.create_run(
            db,
            IngestionRunCreate(
                provider=provider.provider_name,
                entity_type=entity_type,
                status="running",
                started_at=now,
                cursor_from=since,
            ),
        )

        logger.info(
            "ingestion start provider=%s entity=%s since=%s",
            provider.provider_name, entity_type, since.isoformat(),
        )

        try:
            fetched, upserted = await self._run_sync(db, provider, entity_type, since)
            self._run_repo.update_run(
                db,
                run.id,
                IngestionRunUpdate(
                    status="completed",
                    completed_at=datetime.now(timezone.utc),
                    records_fetched=fetched,
                    records_upserted=upserted,
                    cursor_to=now,
                ),
            )
            logger.info(
                "ingestion done provider=%s entity=%s fetched=%d upserted=%d",
                provider.provider_name, entity_type, fetched, upserted,
            )
        except Exception as exc:
            self._run_repo.update_run(
                db,
                run.id,
                IngestionRunUpdate(
                    status="failed",
                    completed_at=datetime.now(timezone.utc),
                    error_message=str(exc),
                ),
            )
            logger.error(
                "ingestion failed provider=%s entity=%s error=%s",
                provider.provider_name, entity_type, exc,
            )
            raise

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_cursor(self, db: Session, provider: str, entity_type: str) -> datetime:
        last_run = self._run_repo.get_last_successful(db, provider, entity_type)
        if last_run and last_run.cursor_to:
            return last_run.cursor_to
        return datetime.now(timezone.utc) - timedelta(hours=_DEFAULT_LOOKBACK_HOURS)

    async def _run_sync(
        self, db: Session, provider: BaseProvider, entity_type: str, since: datetime
    ) -> tuple[int, int]:
        if entity_type == "truck":
            return await self._sync_trucks(db, provider, since)
        if entity_type == "driver":
            return await self._sync_drivers(db, provider, since)
        if entity_type == "telemetry":
            return await self._sync_telemetry(db, provider, since)
        raise ValueError(f"Unknown entity_type: {entity_type!r}")

    async def _sync_trucks(
        self, db: Session, provider: BaseProvider, since: datetime
    ) -> tuple[int, int]:
        raw_list = await provider.fetch_vehicles(since)
        now = datetime.now(timezone.utc)
        for raw in raw_list:
            truck_create, provider_id = provider.map_vehicle(raw)
            self._truck_repo.upsert_from_provider(
                db, truck_create, provider.provider_name, provider_id, ingested_at=now
            )
        return len(raw_list), len(raw_list)

    async def _sync_drivers(
        self, db: Session, provider: BaseProvider, since: datetime
    ) -> tuple[int, int]:
        raw_list = await provider.fetch_drivers(since)
        now = datetime.now(timezone.utc)
        for raw in raw_list:
            driver_create, provider_id = provider.map_driver(raw)
            self._driver_repo.upsert_from_provider(
                db, driver_create, provider.provider_name, provider_id, ingested_at=now
            )
        return len(raw_list), len(raw_list)

    async def _sync_telemetry(
        self, db: Session, provider: BaseProvider, since: datetime
    ) -> tuple[int, int]:
        raw_list = await provider.fetch_locations(since)
        if not raw_list:
            return 0, 0

        # Resolve provider vehicle IDs → internal truck_ids in one query.
        vehicle_ids = list({str(r["vehicle"]["id"]) for r in raw_list})
        truck_map = self._truck_repo.get_trucks_by_provider_ids(
            db, provider.provider_name, vehicle_ids
        )

        now = datetime.now(timezone.utc)
        upserted = 0
        skipped = 0
        for raw in raw_list:
            vehicle_id = str(raw["vehicle"]["id"])
            truck_id = truck_map.get(vehicle_id)
            if not truck_id:
                skipped += 1
                continue
            event_create, provider_id = provider.map_location(raw, truck_id)
            self._telemetry_repo.upsert_from_provider(
                db, event_create, provider.provider_name, provider_id, ingested_at=now
            )
            upserted += 1

        if skipped:
            logger.warning(
                "telemetry sync skipped %d location(s) with no matching truck "
                "for provider=%s. Ensure trucks are synced before telemetry.",
                skipped, provider.provider_name,
            )

        return len(raw_list), upserted


ingestion_service = IngestionService()
