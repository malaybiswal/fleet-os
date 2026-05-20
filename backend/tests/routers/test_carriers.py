from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import delete

from app.models import Carrier, CarrierSnapshot, OutreachNote, Tag
from app.models.carrier import carrier_tags


def _clear(db):
    db.execute(delete(carrier_tags))
    db.query(OutreachNote).delete()
    db.query(CarrierSnapshot).delete()
    db.query(Carrier).delete()
    db.query(Tag).delete()
    db.commit()


@pytest.fixture(autouse=True)
def clean_db(db):
    _clear(db)
    yield
    _clear(db)


def make_carrier(db, **overrides):
    values = {
        "dot_number": "DOT-1",
        "mc_number": "MC-1",
        "legal_name": "Swift Test Carrier",
        "city": "Austin",
        "state": "TX",
        "authority_status": "active",
        "authority_date": date(2026, 1, 1),
        "power_units": 10,
        "driver_count": 12,
        "outreach_status": "not_contacted",
    }
    values.update(overrides)
    carrier = Carrier(**values)
    db.add(carrier)
    db.commit()
    db.refresh(carrier)
    return carrier


def make_tag(db, name="reefer"):
    tag = Tag(name=name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


# --- Carrier list ---
def test_list_carriers_returns_200(client):
    response = client.get("/carriers")

    assert response.status_code == 200
    assert response.json() == {"data": [], "total": 0, "page": 1, "page_size": 50}


def test_list_carriers_filter_by_state(client, db):
    make_carrier(db, dot_number="DOT-TX", legal_name="Texas Carrier", state="TX")
    make_carrier(db, dot_number="DOT-OK", legal_name="Oklahoma Carrier", state="OK")

    response = client.get("/carriers?state=TX")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["data"][0]["state"] == "TX"


def test_list_carriers_filter_by_outreach_status(client, db):
    make_carrier(db, dot_number="DOT-1", outreach_status="contacted")
    make_carrier(db, dot_number="DOT-2", outreach_status="not_contacted")

    response = client.get("/carriers?outreach_status=contacted")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["data"][0]["outreach_status"] == "contacted"


def test_list_carriers_pagination(client, db):
    make_carrier(db, dot_number="DOT-1", legal_name="Carrier 1")
    make_carrier(db, dot_number="DOT-2", legal_name="Carrier 2")
    make_carrier(db, dot_number="DOT-3", legal_name="Carrier 3")

    response = client.get("/carriers?page=2&page_size=1")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["page"] == 2
    assert body["page_size"] == 1
    assert len(body["data"]) == 1


# --- Search ---
def test_search_carriers_by_name(client, db):
    make_carrier(db, legal_name="Swift Transportation")
    make_carrier(db, dot_number="DOT-2", legal_name="Other Carrier")

    response = client.get("/carriers/search?q=swift")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["data"][0]["legal_name"] == "Swift Transportation"


def test_search_carriers_requires_q_param(client):
    response = client.get("/carriers/search")

    assert response.status_code == 422


# --- New ---
def test_new_carriers_returns_recent(client, db):
    make_carrier(
        db,
        dot_number="DOT-NEW",
        legal_name="Recent Carrier",
        created_at=datetime.utcnow() - timedelta(days=5),
    )
    make_carrier(
        db,
        dot_number="DOT-OLD",
        legal_name="Old Carrier",
        created_at=datetime.utcnow() - timedelta(days=60),
    )

    response = client.get("/carriers/new?days=30")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["data"][0]["legal_name"] == "Recent Carrier"


# --- Detail ---
def test_get_carrier_returns_full_record(client, db):
    carrier = make_carrier(db)

    response = client.get(f"/carriers/{carrier.id}")

    assert response.status_code == 200
    assert response.json()["id"] == carrier.id
    assert response.json()["dot_number"] == "DOT-1"


def test_get_carrier_404_on_missing(client):
    response = client.get("/carriers/999999")

    assert response.status_code == 404


# --- Outreach status ---
def test_patch_outreach_status_valid(client, db):
    carrier = make_carrier(db)

    response = client.patch(
        f"/carriers/{carrier.id}/outreach-status",
        json={"status": "contacted"},
    )

    assert response.status_code == 200
    assert response.json()["outreach_status"] == "contacted"


def test_patch_outreach_status_invalid_value(client, db):
    carrier = make_carrier(db)

    response = client.patch(
        f"/carriers/{carrier.id}/outreach-status",
        json={"status": "invalid"},
    )

    assert response.status_code == 422


# --- Notes ---
def test_create_note(client, db):
    carrier = make_carrier(db)

    response = client.post(
        f"/carriers/{carrier.id}/notes",
        json={"content": "Called dispatcher, left voicemail"},
    )

    assert response.status_code == 201
    assert response.json()["content"] == "Called dispatcher, left voicemail"


def test_list_notes_ordered_newest_first(client, db):
    carrier = make_carrier(db)
    older = OutreachNote(
        carrier_id=carrier.id,
        note="Older note",
        created_at=datetime.utcnow() - timedelta(days=1),
    )
    newer = OutreachNote(
        carrier_id=carrier.id,
        note="Newer note",
        created_at=datetime.utcnow(),
    )
    db.add_all([older, newer])
    db.commit()

    response = client.get(f"/carriers/{carrier.id}/notes")

    assert response.status_code == 200
    assert [note["content"] for note in response.json()] == ["Newer note", "Older note"]


def test_update_note(client, db):
    carrier = make_carrier(db)
    note = OutreachNote(carrier_id=carrier.id, note="Old content")
    db.add(note)
    db.commit()
    db.refresh(note)

    response = client.patch(
        f"/carriers/{carrier.id}/notes/{note.id}",
        json={"content": "Updated content"},
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Updated content"


def test_delete_note(client, db):
    carrier = make_carrier(db)
    note = OutreachNote(carrier_id=carrier.id, note="Delete me")
    db.add(note)
    db.commit()
    db.refresh(note)

    response = client.delete(f"/carriers/{carrier.id}/notes/{note.id}")

    assert response.status_code == 204
    assert db.query(OutreachNote).filter(OutreachNote.id == note.id).first() is None


def test_delete_note_wrong_carrier_returns_404(client, db):
    carrier = make_carrier(db, dot_number="DOT-1")
    other = make_carrier(db, dot_number="DOT-2")
    note = OutreachNote(carrier_id=carrier.id, note="Wrong carrier")
    db.add(note)
    db.commit()
    db.refresh(note)

    response = client.delete(f"/carriers/{other.id}/notes/{note.id}")

    assert response.status_code == 404


# --- Tags ---
def test_add_tag_to_carrier(client, db):
    carrier = make_carrier(db)
    tag = make_tag(db)

    response = client.post(f"/carriers/{carrier.id}/tags", json={"tag_id": tag.id})

    assert response.status_code == 201
    assert response.json()[0]["name"] == "reefer"


def test_remove_tag_from_carrier(client, db):
    carrier = make_carrier(db)
    tag = make_tag(db)
    carrier.tags.append(tag)
    db.commit()

    response = client.delete(f"/carriers/{carrier.id}/tags/{tag.id}")

    assert response.status_code == 204
    assert carrier.tags == []


def test_remove_nonexistent_tag_returns_404(client, db):
    carrier = make_carrier(db)

    response = client.delete(f"/carriers/{carrier.id}/tags/999999")

    assert response.status_code == 404


# --- Stats ---
def test_get_carrier_stats_returns_snapshots(client, db):
    carrier = make_carrier(db)
    db.add_all(
        [
            CarrierSnapshot(
                carrier_id=carrier.id,
                snapshot_date=date(2026, 5, 2),
                power_units=12,
            ),
            CarrierSnapshot(
                carrier_id=carrier.id,
                snapshot_date=date(2026, 5, 1),
                power_units=10,
            ),
        ]
    )
    db.commit()

    response = client.get(f"/carriers/{carrier.id}/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["carrier_id"] == carrier.id
    assert [snapshot["snapshot_date"] for snapshot in body["snapshots"]] == [
        "2026-05-01",
        "2026-05-02",
    ]


def test_get_carrier_stats_404_on_missing(client):
    response = client.get("/carriers/999999/stats")

    assert response.status_code == 404
