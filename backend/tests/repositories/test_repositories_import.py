from app.repositories import (
    AlertRepository,
    DashboardRepository,
    DwellRepository,
    LoadRepository,
    TelemetryRepository,
    TruckRepository,
)


def test_repository_imports():
    assert AlertRepository is not None
    assert DashboardRepository is not None
    assert DwellRepository is not None
    assert LoadRepository is not None
    assert TelemetryRepository is not None
    assert TruckRepository is not None