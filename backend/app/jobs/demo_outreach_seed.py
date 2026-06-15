"""Spread existing carriers across the outreach pipeline for demos.

This is intentionally separate from ``app.seed.demo_environment``: the deterministic
demo reset only owns ``DEMO-`` fleet rows and does NOT manage carrier rows (carriers
come from FMCSA ingestion). This job is non-destructive to carrier identity — it only
sets ``outreach_status`` and adds/clears outreach *notes* — so a freshly ingested,
all-``not_contacted`` carrier table becomes a believable CRM board.

Re-running is safe: it first removes the contact-attempt notes it previously created
(notes whose ``outcome`` is a contact method), then re-applies a deterministic spread.
"""

import argparse

from sqlalchemy import case

from app.database import SessionLocal
from app.models import Carrier, OutreachNote
from app.repositories.carrier_repository import CONTACT_OUTCOMES, log_contact
from app.schemas.carrier import LogContactRequest

# Deterministic round-robin of (status, number_of_logged_attempts) applied to the
# top carriers by lead score so every column on the board is populated.
PIPELINE_PLAN: list[tuple[str, int]] = [
    ("not_contacted", 0),
    ("contacted", 1),
    ("follow_up", 2),
    ("converted", 3),
    ("not_interested", 1),
    ("contacted", 2),
    ("follow_up", 1),
    ("not_contacted", 0),
]

ATTEMPT_METHODS = ["call", "email", "sms"]


def seed_demo_outreach(db, *, limit: int = 24) -> dict[str, int]:
    carriers = (
        db.query(Carrier)
        .order_by(
            case((Carrier.lead_score.is_(None), 1), else_=0),
            Carrier.lead_score.desc(),
            Carrier.id.asc(),
        )
        .limit(limit)
        .all()
    )

    # Clear previously seeded contact notes so attempt counts stay stable across runs.
    carrier_ids = [c.id for c in carriers]
    cleared = 0
    if carrier_ids:
        cleared = (
            db.query(OutreachNote)
            .filter(
                OutreachNote.carrier_id.in_(carrier_ids),
                OutreachNote.outcome.in_(CONTACT_OUTCOMES),
            )
            .delete(synchronize_session=False)
        )
        db.commit()

    counts: dict[str, int] = {}
    for index, carrier in enumerate(carriers):
        status, attempts = PIPELINE_PLAN[index % len(PIPELINE_PLAN)]
        carrier.outreach_status = status
        db.commit()
        for attempt in range(attempts):
            method = ATTEMPT_METHODS[attempt % len(ATTEMPT_METHODS)]
            log_contact(
                db,
                carrier.id,
                LogContactRequest(method=method, advance_status=False),
            )
        counts[status] = counts.get(status, 0) + 1

    return {"carriers": len(carriers), "notes_cleared": cleared, **counts}


def main(argv: list[str] | None = None, session_factory=SessionLocal) -> int:
    parser = argparse.ArgumentParser(
        description="Spread existing carriers across the outreach pipeline for demos"
    )
    parser.add_argument("--limit", type=int, default=24)
    args = parser.parse_args(argv)

    db = session_factory()
    try:
        counts = seed_demo_outreach(db, limit=args.limit)
    finally:
        db.close()

    summary = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
    print(f"Demo outreach seed complete: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
