from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.dwell_event import DwellEvent
from app.services.dwell_service import DwellService


def test_calculate_dwell_hours():
    service = DwellService()

    arrival = datetime(2026, 5, 10, 8, 0, tzinfo=timezone.utc)
    departure = datetime(2026, 5, 10, 13, 30, tzinfo=timezone.utc)

    assert service.calculate_dwell_hours(arrival, departure) == 5.5


def test_calculate_loading_delay():
    service = DwellService()

    appointment = datetime(2026, 5, 10, 8, 0, tzinfo=timezone.utc)
    loading_start = datetime(2026, 5, 10, 10, 0, tzinfo=timezone.utc)

    assert service.calculate_loading_delay(appointment, loading_start) == 2.0


def test_calculate_facility_score():
    service = DwellService()

    assert service.calculate_facility_score(2) == 80
    assert service.calculate_facility_score(5) == 50
    assert service.calculate_facility_score(10) == 0
    assert service.calculate_facility_score(12) == 0


def test_create_dwell_event_rejects_arrival_after_departure():
    service = DwellService()

    dwell_event = DwellEvent(
        load_id="TEST-LOAD-INVALID",
        arrival_time=datetime(2026, 5, 10, 14, 0, tzinfo=timezone.utc),
        departure_time=datetime(2026, 5, 10, 13, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_dwell_event(db=None, dwell_event=dwell_event)

    assert exc_info.value.status_code == 422
    assert "arrival_time must be before departure_time" in exc_info.value.detail