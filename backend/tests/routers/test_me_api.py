from app.config import settings


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
