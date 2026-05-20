from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.jobs.carrier_ingestion import run_company_census_ingest
from app.models import Carrier, CarrierSnapshot


class CountingSession(Session):
    commits = 0

    def commit(self):
        CountingSession.commits += 1
        return super().commit()


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, class_=CountingSession)
    CountingSession.commits = 0
    return TestingSessionLocal()


def census_record(dot_number="1001", legal_name="TEST CARRIER", **overrides):
    record = {
        "dot_number": dot_number,
        "legal_name": legal_name,
        "status_code": "A",
        "add_date": "20250101",
        "power_units": "3",
        "total_drivers": "4",
        "phy_state": "TX",
        "crgo_genfreight": "X",
    }
    record.update(overrides)
    return record


# Tests that a full FMCSA ingest creates one carrier and one daily snapshot, then
# re-running the same dataset for the same date updates instead of duplicating rows.
def test_bulk_ingest_writes_carriers_and_snapshots_idempotently():
    db = make_db()

    try:
        def fetch_page(limit, offset, filters=None):
            if offset == 0:
                return [census_record()]
            return []

        first_result = run_company_census_ingest(
            db,
            page_size=10,
            snapshot_date=date(2026, 5, 20),
            fetch_page=fetch_page,
        )
        second_result = run_company_census_ingest(
            db,
            page_size=10,
            snapshot_date=date(2026, 5, 20),
            fetch_page=fetch_page,
        )

        assert first_result.upserted == 1
        assert second_result.upserted == 1
        assert db.query(Carrier).count() == 1
        assert db.query(CarrierSnapshot).count() == 1
    finally:
        db.close()


# Tests that a same-day FMCSA rerun updates carrier fields and replaces the
# matching snapshot's metrics and raw payload.
def test_same_day_rerun_overwrites_snapshot_raw_payload():
    db = make_db()

    try:
        records = [
            census_record(legal_name="TEST CARRIER", power_units="3"),
            census_record(legal_name="TEST CARRIER UPDATED", power_units="8"),
        ]

        def fetch_first(limit, offset, filters=None):
            return [records[0]] if offset == 0 else []

        def fetch_second(limit, offset, filters=None):
            return [records[1]] if offset == 0 else []

        run_company_census_ingest(
            db,
            page_size=10,
            snapshot_date=date(2026, 5, 20),
            fetch_page=fetch_first,
        )
        run_company_census_ingest(
            db,
            page_size=10,
            snapshot_date=date(2026, 5, 20),
            fetch_page=fetch_second,
        )

        carrier = db.query(Carrier).one()
        snapshot = db.query(CarrierSnapshot).one()
        assert carrier.legal_name == "TEST CARRIER UPDATED"
        assert carrier.power_units == 8
        assert snapshot.power_units == 8
        assert snapshot.raw_payload["legal_name"] == "TEST CARRIER UPDATED"
    finally:
        db.close()


# Tests that batched FMCSA ingest commits each valid batch, skips malformed
# records, records the skip count, and writes only valid carriers/snapshots.
def test_bulk_ingest_commits_per_batch_and_skips_malformed_records(caplog):
    db = make_db()

    try:
        pages = {
            0: [census_record(dot_number="1001"), {"dot_number": "1002"}],
            2: [census_record(dot_number="1003")],
            3: [],
        }

        def fetch_page(limit, offset, filters=None):
            return pages[offset]

        result = run_company_census_ingest(
            db,
            page_size=2,
            snapshot_date=date(2026, 5, 20),
            fetch_page=fetch_page,
        )

        assert result.fetched == 3
        assert result.upserted == 2
        assert result.skipped == 1
        assert result.batches_committed == 2
        assert CountingSession.commits == 2
        assert db.query(Carrier).count() == 2
        assert db.query(CarrierSnapshot).count() == 2
        assert "Skipping malformed FMCSA carrier record" in caplog.text
    finally:
        db.close()
