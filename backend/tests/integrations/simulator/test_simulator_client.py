from app.integrations.simulator.client import fetch_simulated_vehicle_payloads
from app.services.operational_status import (
    OperationalStatus,
    derive_operational_status,
)


def _all_payloads(iterations: int = 200) -> list[dict]:
    payloads: list[dict] = []
    for _ in range(iterations):
        payloads.extend(fetch_simulated_vehicle_payloads())
    return payloads


def test_simulator_payload_status_is_consistent_with_speed():
    for payload in _all_payloads():
        expected = derive_operational_status(
            speed_mph=payload["speed_mph"],
            reported_status=(
                "maintenance"
                if payload["status"] == OperationalStatus.MAINTENANCE.value
                else None
            ),
        )
        assert payload["status"] == expected


def test_simulator_never_emits_legacy_active_status():
    statuses = {payload["status"] for payload in _all_payloads()}

    assert "active" not in statuses
    assert statuses <= {status.value for status in OperationalStatus}


def test_simulator_maintenance_payloads_report_zero_speed():
    for payload in _all_payloads():
        if payload["status"] == OperationalStatus.MAINTENANCE.value:
            assert payload["speed_mph"] == 0
            assert payload["heading"] == 0
