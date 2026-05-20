from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Mapping

from sqlalchemy.orm import Session

from app.config import settings
from app.importers.fmcsa_carriers import (
    MalformedCarrierRecord,
    fetch_socrata_page,
    transform_company_census_record,
)
from app.repositories.carrier_repository import upsert_carrier, upsert_carrier_snapshot

logger = logging.getLogger(__name__)

FetchPage = Callable[..., list[dict[str, Any]]]


@dataclass
class CarrierIngestionResult:
    fetched: int = 0
    upserted: int = 0
    skipped: int = 0
    batches_committed: int = 0


def run_company_census_ingest(
    db: Session,
    *,
    record_cap: int | None = None,
    filters: Mapping[str, str | int] | None = None,
    page_size: int | None = None,
    snapshot_date: date | None = None,
    fetch_page: FetchPage = fetch_socrata_page,
) -> CarrierIngestionResult:
    effective_page_size = page_size or settings.FMCSA_PAGE_SIZE
    effective_snapshot_date = snapshot_date or date.today()
    offset = 0
    result = CarrierIngestionResult()

    while True:
        limit = _page_limit(effective_page_size, record_cap, result.fetched)
        if limit <= 0:
            break

        records = fetch_page(limit=limit, offset=offset, filters=filters)
        if not records:
            break

        logger.info(
            "Fetched %s FMCSA carrier records at offset %s",
            len(records),
            offset,
        )

        for record in records:
            result.fetched += 1
            try:
                carrier_create = transform_company_census_record(record)
            except MalformedCarrierRecord as exc:
                result.skipped += 1
                logger.warning("Skipping malformed FMCSA carrier record: %s", exc)
                continue

            carrier = upsert_carrier(db, carrier_create)
            upsert_carrier_snapshot(
                db,
                carrier=carrier,
                snapshot_date=effective_snapshot_date,
                raw_payload=dict(record),
            )
            result.upserted += 1

        db.commit()
        result.batches_committed += 1
        logger.info(
            "Committed FMCSA carrier ingestion batch: fetched=%s upserted=%s skipped=%s",
            result.fetched,
            result.upserted,
            result.skipped,
        )

        if len(records) < limit:
            break

        offset += len(records)

    return result


def _page_limit(page_size: int, record_cap: int | None, fetched: int) -> int:
    if record_cap is None:
        return page_size
    return min(page_size, max(record_cap - fetched, 0))
