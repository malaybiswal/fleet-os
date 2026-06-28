import jwt

from app.config import settings
from app.models.fleet import Fleet
from app.models.user import User


def test_get_me_adopts_existing_user_by_email(client, db):
    fleet = Fleet(name="Demo Fleet")
    db.add(fleet)
    db.flush()

    seeded_user = User(
        firebase_uid="demo-seed-pribiswal7@gmail.com",
        email="pribiswal7@gmail.com",
        fleet_id=fleet.id,
        role="admin",
    )
    db.add(seeded_user)
    db.commit()

    token = jwt.encode(
        {
            "user_id": "real-firebase-uid",
            "email": "pribiswal7@gmail.com",
            "name": "Priyansu Biswal",
        },
        "unused-secret",
        algorithm="HS256",
    )

    response = client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()
    db.refresh(seeded_user)

    assert data["id"] == seeded_user.id
    assert data["email"] == "pribiswal7@gmail.com"
    assert data["firebase_uid"] == "real-firebase-uid"
    assert data["fleet_id"] == fleet.id
    assert seeded_user.firebase_uid == "real-firebase-uid"
    assert seeded_user.name == "Priyansu Biswal"
    assert (
        db.query(User)
        .filter(User.email == "pribiswal7@gmail.com")
        .count()
        == 1
    )


def test_get_me_resolves_real_user_when_auth_disabled(client):
    token = jwt.encode(
        {"user_id": "some-uid", "email": "someone.else@gmail.com", "name": "Someone Else"},
        "unused-secret",
        algorithm="HS256",
    )

    response = client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "someone.else@gmail.com"
    assert data["firebase_uid"] == "some-uid"
    assert data["email"] != "dev@fleetos.local"


def test_get_me_requires_authorization_when_auth_enabled(client, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)

    response = client.get("/api/me")

    print(response.status_code)
    print(response.json())

    assert response.status_code == 401

def test_get_me_returns_current_dev_user(client):
    response = client.get("/api/me")

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "dev@fleetos.local"
    assert data["firebase_uid"] == "dev-user"
    assert data["role"] == "admin"
    assert isinstance(data["fleet_id"], int)
