from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_dwell_events():
    response = client.get("/api/dwell/events")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_facility_scorecard():
    response = client.get("/api/dwell/facility-scorecard")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_broker_scorecard():
    response = client.get("/api/dwell/broker-scorecard")

    assert response.status_code == 200
    assert isinstance(response.json(), list)