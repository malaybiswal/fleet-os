import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base
from app.jobs import demo_outreach_seed
from app.models.carrier import Carrier, OutreachNote


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _make_carriers(db, count):
    for i in range(count):
        db.add(
            Carrier(
                dot_number=f"DOT-{i}",
                legal_name=f"Carrier {i}",
                lead_score=100 - i,
                outreach_status="not_contacted",
            )
        )
    db.commit()


def test_seed_spreads_carriers_across_pipeline_stages(db):
    _make_carriers(db, 8)

    demo_outreach_seed.seed_demo_outreach(db, limit=8)

    statuses = {c.outreach_status for c in db.query(Carrier).all()}
    # The deterministic plan touches every pipeline stage.
    assert statuses == {
        "not_contacted",
        "contacted",
        "follow_up",
        "converted",
        "not_interested",
    }


def test_seed_creates_contact_notes(db):
    _make_carriers(db, 8)

    demo_outreach_seed.seed_demo_outreach(db, limit=8)

    assert db.query(OutreachNote).count() > 0


def test_seed_is_idempotent_on_attempt_counts(db):
    _make_carriers(db, 8)

    demo_outreach_seed.seed_demo_outreach(db, limit=8)
    first = db.query(OutreachNote).count()
    demo_outreach_seed.seed_demo_outreach(db, limit=8)
    second = db.query(OutreachNote).count()

    assert first == second
