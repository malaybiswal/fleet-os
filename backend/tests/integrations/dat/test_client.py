import pytest

from app.integrations.dat.client import (
    DatAuthenticationError,
    DatCredentials,
    MockDatProvider,
)
from app.integrations.dat.mapper import map_dat_load_to_normalized
from app.seed.scenarios import STRATEGIC_LOAD_SCENARIOS


def _provider(**kwargs) -> MockDatProvider:
    kwargs.setdefault("username", "demo")
    kwargs.setdefault("password", "secret")
    return MockDatProvider(DatCredentials(**kwargs))


def test_mock_provider_postings_derive_from_scenarios():
    postings = _provider().search_loads()

    assert len(postings) == len(STRATEGIC_LOAD_SCENARIOS)
    assert {posting["id"] for posting in postings} == {
        f"MOCK-DAT-demo-{scenario.key}" for scenario in STRATEGIC_LOAD_SCENARIOS
    }


def test_mock_provider_results_are_tenant_specific():
    fleet_a = _provider(username="fleet-a").search_loads()
    fleet_b = _provider(username="fleet-b").search_loads()

    ids_a = {posting["id"] for posting in fleet_a}
    ids_b = {posting["id"] for posting in fleet_b}

    # Different tenants never receive the same listings.
    assert ids_a.isdisjoint(ids_b)
    assert all(pid.startswith("MOCK-DAT-fleet-a-") for pid in ids_a)


def test_mock_provider_honors_equipment_filter():
    postings = _provider(filters={"equipment_type": "Reefer"}).search_loads()

    assert postings
    assert all(posting["equipment"] == "Reefer" for posting in postings)
    assert len(postings) < len(STRATEGIC_LOAD_SCENARIOS)


def test_mock_provider_call_filters_override_saved_filters():
    provider = _provider(filters={"equipment_type": "Reefer"})

    postings = provider.search_loads({"equipment_type": "Flatbed"})

    assert postings
    assert all(posting["equipment"] == "Flatbed" for posting in postings)


def test_mock_provider_postings_round_trip_through_mapper():
    for posting in _provider().search_loads():
        normalized = map_dat_load_to_normalized(posting, fleet_id=8)

        assert normalized.source == "dat"
        assert normalized.gross_revenue > 0
        assert normalized.total_miles > 0
        assert normalized.origin
        assert normalized.destination


def test_mock_provider_requires_credentials():
    provider = MockDatProvider(DatCredentials(username="", password=""))

    with pytest.raises(DatAuthenticationError):
        provider.search_loads()
