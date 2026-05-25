from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Callable, Mapping

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.importers.fmcsa_carriers import (
    MalformedCarrierRecord,
    fetch_socrata_page,
    transform_company_census_record,
)
from app.repositories.carrier_repository import upsert_carrier, upsert_carrier_snapshot

logger = logging.getLogger(__name__)

FetchPage = Callable[..., list[dict[str, Any]]]

AUTHORITY_STATUS_FILTERS = {
    "active": "A",
    "inactive": "I",
    "pending": "P",
}
DEFAULT_RECORD_CAP = 5_000
DEFAULT_AUTHORITY_STATUS = "active"
DEFAULT_AUTHORITY_AGE_DAYS = 365
DEFAULT_MIN_POWER_UNITS = 1
DEFAULT_MAX_POWER_UNITS = 50
DEFAULT_SOURCE_ORDER = "add_date DESC, dot_number ASC"


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
    source_order: str | None = None,
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

        if source_order:
            records = fetch_page(
                limit=limit,
                offset=offset,
                filters=filters,
                order=source_order,
            )
        else:
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


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(levelname)s:%(name)s:%(message)s",
    )

    db = SessionLocal()
    try:
        result = run_company_census_ingest(
            db,
            record_cap=_effective_record_cap(args),
            filters=_build_socrata_filters(args),
            page_size=args.page_size,
            source_order=DEFAULT_SOURCE_ORDER,
        )
    except Exception:
        logger.exception("Carrier ingestion failed")
        return 1
    finally:
        db.close()

    print(
        "Carrier ingestion complete: "
        f"fetched={result.fetched} "
        f"upserted={result.upserted} "
        f"skipped={result.skipped} "
        f"batches_committed={result.batches_committed}"
    )
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import FMCSA Company Census carriers into FleetOS",
    )
    parser.add_argument(
        "--record-cap",
        type=_positive_int,
        help="Maximum number of records to fetch and process",
    )
    parser.add_argument(
        "--no-record-cap",
        action="store_true",
        help="Disable the modern default record cap unless --record-cap is provided",
    )
    parser.add_argument(
        "--state",
        type=_state_code,
        help="Two-letter physical state filter, for example TX",
    )
    parser.add_argument(
        "--page-size",
        type=_positive_int,
        default=settings.FMCSA_PAGE_SIZE,
        help="FMCSA API page size and database commit batch size",
    )
    parser.add_argument(
        "--authority-status",
        choices=(*AUTHORITY_STATUS_FILTERS.keys(), "any"),
        help="FMCSA authority status filter",
    )
    parser.add_argument(
        "--authority-age-days",
        type=_non_negative_int,
        help="Maximum authority age in days based on FMCSA add_date",
    )
    parser.add_argument(
        "--no-authority-age-limit",
        action="store_true",
        help=(
            "Disable the modern default authority-age limit unless "
            "--authority-age-days is provided"
        ),
    )
    parser.add_argument(
        "--min-power-units",
        type=_non_negative_int,
        help="Minimum power-unit count to ingest",
    )
    parser.add_argument(
        "--max-power-units",
        type=_non_negative_int,
        help="Maximum power-unit count to ingest",
    )
    parser.add_argument(
        "--no-power-unit-limit",
        action="store_true",
        help=(
            "Disable the modern default power-unit bounds unless "
            "--min-power-units or --max-power-units are provided"
        ),
    )
    parser.add_argument(
        "--log-level",
        choices=("debug", "info", "warning", "error"),
        default="info",
        help="Logging verbosity for the CLI run",
    )

    args = parser.parse_args(argv)
    if (
        _effective_min_power_units(args) is not None
        and _effective_max_power_units(args) is not None
        and _effective_min_power_units(args) > _effective_max_power_units(args)
    ):
        parser.error("--min-power-units cannot exceed --max-power-units")
    return args


def _build_socrata_filters(args: argparse.Namespace) -> dict[str, str] | None:
    filters: dict[str, str] = {}
    where_clauses: list[str] = []
    authority_status = _effective_authority_status(args)
    min_power_units = _effective_min_power_units(args)
    max_power_units = _effective_max_power_units(args)
    authority_age_days = _effective_authority_age_days(args)

    if args.state:
        filters["phy_state"] = args.state
    if authority_status:
        filters["status_code"] = AUTHORITY_STATUS_FILTERS[authority_status]
    if min_power_units is not None:
        where_clauses.append(f"power_units::number >= {min_power_units}")
    if max_power_units is not None:
        where_clauses.append(f"power_units::number <= {max_power_units}")
    if authority_age_days is not None:
        cutoff = date.today() - timedelta(days=authority_age_days)
        where_clauses.append(f"add_date >= '{cutoff:%Y%m%d}'")
    if where_clauses:
        filters["$where"] = " AND ".join(where_clauses)

    return filters or None


def _effective_record_cap(args: argparse.Namespace) -> int | None:
    if args.record_cap is not None:
        return args.record_cap
    return None if args.no_record_cap else DEFAULT_RECORD_CAP


def _effective_authority_status(args: argparse.Namespace) -> str | None:
    if args.authority_status == "any":
        return None
    return args.authority_status or DEFAULT_AUTHORITY_STATUS


def _effective_authority_age_days(args: argparse.Namespace) -> int | None:
    if args.authority_age_days is not None:
        return args.authority_age_days
    return None if args.no_authority_age_limit else DEFAULT_AUTHORITY_AGE_DAYS


def _effective_min_power_units(args: argparse.Namespace) -> int | None:
    if args.min_power_units is not None:
        return args.min_power_units
    return None if args.no_power_unit_limit else DEFAULT_MIN_POWER_UNITS


def _effective_max_power_units(args: argparse.Namespace) -> int | None:
    if args.max_power_units is not None:
        return args.max_power_units
    return None if args.no_power_unit_limit else DEFAULT_MAX_POWER_UNITS


def _positive_int(value: str) -> int:
    parsed = _int_value(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _non_negative_int(value: str) -> int:
    parsed = _int_value(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def _int_value(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc


def _state_code(value: str) -> str:
    state = value.strip().upper()
    if len(state) != 2 or not state.isalpha():
        raise argparse.ArgumentTypeError("must be a two-letter state code")
    return state


if __name__ == "__main__":
    raise SystemExit(main())
