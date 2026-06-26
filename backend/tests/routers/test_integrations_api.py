from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.dependencies.fleet import get_current_fleet_id
from app.main import app
from app.models.fleet import Fleet
from app.models.fleet_integration import FleetIntegration


TEST_DATABASE_URL = "sqlite:///./test_integrations_api.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _client_for_fleet(monkeypatch):
    monkeypatch.setattr(settings, "CREDENTIAL_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setattr(settings, "DAT_PROVIDER_MODE", "mock")
    db = TestingSessionLocal()
    fleet = Fleet(name="DAT API Fleet")
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    fleet_id = fleet.id
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_fleet_id] = lambda: fleet_id
    return TestClient(app), fleet_id


def test_dat_credentials_status_omits_secrets(monkeypatch):
    client, fleet_id = _client_for_fleet(monkeypatch)

    response = client.put(
        "/api/integrations/dat",
        json={
            "username": "dat-user",
            "password": "dat-password",
            "filters": {"origin_state": "TX"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["status"] == "connected"
    assert "password" not in body
    assert "username" not in body

    status_response = client.get("/api/integrations/dat")
    assert status_response.status_code == 200
    assert "dat-password" not in status_response.text

    db = TestingSessionLocal()
    try:
        integration = (
            db.query(FleetIntegration)
            .filter(FleetIntegration.fleet_id == fleet_id)
            .one()
        )
        assert "dat-password" not in integration.encrypted_credentials
    finally:
        db.close()


def test_dat_mock_connection_and_disconnect(monkeypatch):
    client, _ = _client_for_fleet(monkeypatch)

    client.put(
        "/api/integrations/dat",
        json={"username": "dat-user", "password": "dat-password"},
    )
    test_response = client.post("/api/integrations/dat/test")
    assert test_response.status_code == 200
    assert test_response.json()["success"] is True

    disconnect_response = client.delete("/api/integrations/dat")
    assert disconnect_response.status_code == 200
    assert disconnect_response.json()["connected"] is False
    assert disconnect_response.json()["status"] == "disabled"
