import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import SessionLocal
from app.integrations.ingestion_service import ingestion_service

logger = logging.getLogger("fleet_os.scheduler")

_scheduler = AsyncIOScheduler()

_ENTITY_TYPES = ["truck", "driver", "telemetry"]


async def _run_sync_job(provider_name: str, entity_type: str) -> None:
    """Wrapper that creates a DB session per job execution."""
    from app.integrations.providers.motive.client import MotiveClient

    _providers = {"motive": MotiveClient}
    provider_cls = _providers.get(provider_name)
    if provider_cls is None:
        logger.error("Unknown provider in scheduler job: %s", provider_name)
        return

    provider = provider_cls()
    db = SessionLocal()
    try:
        await ingestion_service.sync_entity(db, provider, entity_type)
    except Exception:
        pass  # error already logged inside sync_entity
    finally:
        db.close()


def _register_motive_jobs() -> None:
    if not settings.MOTIVE_CLIENT_ID or not settings.MOTIVE_ACCESS_TOKEN:
        logger.info(
            "MOTIVE_CLIENT_ID or MOTIVE_ACCESS_TOKEN not set — skipping Motive ingestion jobs"
        )
        return

    for entity_type in _ENTITY_TYPES:
        _scheduler.add_job(
            _run_sync_job,
            "interval",
            minutes=settings.INGESTION_INTERVAL_MINUTES,
            args=["motive", entity_type],
            id=f"ingest_motive_{entity_type}",
            replace_existing=True,
        )
        logger.info(
            "Registered ingestion job: provider=motive entity=%s interval=%dm",
            entity_type, settings.INGESTION_INTERVAL_MINUTES,
        )


def start_scheduler() -> None:
    if not settings.INGESTION_ENABLED:
        logger.info("INGESTION_ENABLED=false — scheduler not started")
        return

    _register_motive_jobs()

    if _scheduler.get_jobs():
        _scheduler.start()
        logger.info("Ingestion scheduler started with %d job(s)", len(_scheduler.get_jobs()))
    else:
        logger.info("No ingestion jobs registered — scheduler not started")


def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Ingestion scheduler stopped")
