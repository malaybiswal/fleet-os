import argparse
from datetime import datetime, timezone

from app.database import SessionLocal
from app.seed.demo_dataset import DEFAULT_BASE_DATE, DEFAULT_DEMO_SEED
from app.seed.persist import (
    SeedResult,
    dry_run_demo_environment,
    reset_demo_environment,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset FleetOS deterministic demo seed data"
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_DEMO_SEED)
    parser.add_argument(
        "--base-date",
        type=parse_base_date,
        default=DEFAULT_BASE_DATE,
        help="UTC demo base date/time, for example 2026-06-01T14:00:00Z",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print rows that would be deleted/created without writing data",
    )
    return parser.parse_args(argv)


def parse_base_date(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def main(argv: list[str] | None = None, session_factory=None) -> int:
    args = parse_args(argv)
    session_factory = session_factory or SessionLocal
    db = session_factory()

    try:
        if args.dry_run:
            result = dry_run_demo_environment(
                db=db,
                seed=args.seed,
                base_date=args.base_date,
            )
        else:
            result = reset_demo_environment(
                db=db,
                seed=args.seed,
                base_date=args.base_date,
            )
        print_result(result)
        return 0
    finally:
        db.close()


def print_result(result: SeedResult) -> None:
    prefix = "Demo seed dry run complete" if result.dry_run else "Demo seed complete"
    delete_label = "Would delete" if result.dry_run else "Deleted"
    create_label = "Would create" if result.dry_run else "Created"

    print(prefix)
    print(f"{delete_label}: {_format_counts(result.deleted)}")
    print(f"{create_label}: {_format_counts(result.created)}")

    if result.fleet_ids:
        fleets = ", ".join(
            f"{name} (id={result.fleet_ids[key]})"
            for key, name in zip(result.fleet_ids.keys(), result.fleet_names)
        )
    else:
        fleets = ", ".join(result.fleet_names)

    print(f"Demo fleets: {fleets}")


def _format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))


if __name__ == "__main__":
    raise SystemExit(main())
