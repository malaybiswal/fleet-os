from datetime import date, datetime, timezone

from app.database import SessionLocal
from app.models import Carrier, CarrierSnapshot, OutreachNote, Tag
from app.schemas import CarrierCreate, CarrierListItem, CarrierRead


TEST_DOT_NUMBERS = ["TEST-DOT-024-1", "TEST-DOT-024-2", "TEST-DOT-024-3"]
TEST_TAG_NAMES = ["task_024_reefer", "task_024_hot_lead"]


def _cleanup(db):
    db.query(Carrier).filter(Carrier.dot_number.in_(TEST_DOT_NUMBERS)).delete(
        synchronize_session=False
    )
    db.query(Tag).filter(Tag.name.in_(TEST_TAG_NAMES)).delete(synchronize_session=False)
    db.commit()


def test_carrier_model_and_schema_imports():
    assert Carrier is not None
    assert CarrierSnapshot is not None
    assert OutreachNote is not None
    assert Tag is not None
    assert CarrierCreate is not None
    assert CarrierRead is not None
    assert CarrierListItem is not None


def test_carrier_relationships_load_snapshots_notes_and_tags():
    db = SessionLocal()

    try:
        _cleanup(db)

        carrier = Carrier(
            dot_number=TEST_DOT_NUMBERS[0],
            mc_number="MC-024-1",
            legal_name="Task 024 Carrier One",
            state="TX",
            authority_status="active",
            authority_date=date(2026, 1, 10),
            power_units=12,
            driver_count=14,
            cargo_types=["reefer", "general_freight"],
            outreach_status="not_contacted",
        )
        snapshot = CarrierSnapshot(
            carrier=carrier,
            snapshot_date=date(2026, 5, 20),
            power_units=12,
            driver_count=14,
            authority_status="active",
            cargo_types=["reefer", "general_freight"],
            raw_payload={"dot_number": TEST_DOT_NUMBERS[0]},
        )
        note = OutreachNote(
            carrier=carrier,
            note="Initial marketing research note.",
            outcome="left_voicemail",
            follow_up_date=datetime(2026, 5, 21, 15, 0, tzinfo=timezone.utc),
            contact_name="Jamie",
            dispatcher_name="Morgan",
            pain_points="Manual dispatch planning",
            created_by="marketing",
        )
        carrier.tags.extend(
            [
                Tag(name=TEST_TAG_NAMES[0], display_name="Reefer"),
                Tag(name=TEST_TAG_NAMES[1], display_name="Hot Lead"),
            ]
        )

        db.add_all([carrier, snapshot, note])
        db.commit()

        saved = db.query(Carrier).filter(Carrier.dot_number == TEST_DOT_NUMBERS[0]).one()

        assert len(saved.snapshots) == 1
        assert saved.snapshots[0].raw_payload == {"dot_number": TEST_DOT_NUMBERS[0]}
        assert len(saved.outreach_notes) == 1
        assert saved.outreach_notes[0].outcome == "left_voicemail"
        assert {tag.name for tag in saved.tags} == set(TEST_TAG_NAMES)

    finally:
        _cleanup(db)
        db.close()


def test_carrier_query_shapes_for_future_dashboard_filters():
    db = SessionLocal()

    try:
        _cleanup(db)

        carriers = [
            Carrier(
                dot_number=TEST_DOT_NUMBERS[0],
                legal_name="Task 024 Texas Active",
                state="TX",
                authority_status="active",
                authority_date=date(2026, 1, 1),
                power_units=5,
                driver_count=5,
                outreach_status="not_contacted",
            ),
            Carrier(
                dot_number=TEST_DOT_NUMBERS[1],
                legal_name="Task 024 Oklahoma Active",
                state="OK",
                authority_status="active",
                authority_date=date(2025, 1, 1),
                power_units=25,
                driver_count=28,
                outreach_status="follow_up",
            ),
            Carrier(
                dot_number=TEST_DOT_NUMBERS[2],
                legal_name="Task 024 Texas Inactive",
                state="TX",
                authority_status="inactive",
                authority_date=date(2024, 1, 1),
                power_units=60,
                driver_count=62,
                outreach_status="not_interested",
            ),
        ]
        db.add_all(carriers)
        db.commit()

        texas_carriers = db.query(Carrier).filter(Carrier.state == "TX").all()
        mid_size_carriers = (
            db.query(Carrier)
            .filter(Carrier.power_units >= 10, Carrier.power_units <= 50)
            .all()
        )
        active_carriers = (
            db.query(Carrier).filter(Carrier.authority_status == "active").all()
        )
        follow_up_carriers = (
            db.query(Carrier).filter(Carrier.outreach_status == "follow_up").all()
        )
        ordered_by_authority_date = (
            db.query(Carrier)
            .filter(Carrier.dot_number.in_(TEST_DOT_NUMBERS))
            .order_by(Carrier.authority_date.asc())
            .all()
        )

        assert {carrier.dot_number for carrier in texas_carriers} == {
            TEST_DOT_NUMBERS[0],
            TEST_DOT_NUMBERS[2],
        }
        assert [carrier.dot_number for carrier in mid_size_carriers] == [
            TEST_DOT_NUMBERS[1]
        ]
        assert {carrier.dot_number for carrier in active_carriers} == {
            TEST_DOT_NUMBERS[0],
            TEST_DOT_NUMBERS[1],
        }
        assert [carrier.dot_number for carrier in follow_up_carriers] == [
            TEST_DOT_NUMBERS[1]
        ]
        assert [carrier.dot_number for carrier in ordered_by_authority_date] == [
            TEST_DOT_NUMBERS[2],
            TEST_DOT_NUMBERS[1],
            TEST_DOT_NUMBERS[0],
        ]

    finally:
        _cleanup(db)
        db.close()
