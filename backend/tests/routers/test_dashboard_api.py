from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_summary_endpoint_returns_expected_shape():
    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()

    assert "active_trucks" in body
    assert "avg_dwell_hours" in body
    assert "total_revenue" in body
    assert "avg_revenue_per_mile" in body
    assert "deadhead_percentage" in body
    assert "open_alerts" in body
    assert "open_loads" in body
    assert "fuel_cost_per_mile" in body


def test_dashboard_summary_accepts_date_filters():
    response = client.get(
        "/api/dashboard/summary",
        params={
            "start_date": "2026-05-01T00:00:00Z",
            "end_date": "2026-05-31T23:59:59Z",
        },
    )

    assert response.status_code == 200