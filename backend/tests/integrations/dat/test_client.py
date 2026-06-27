import httpx
import pytest

from app.integrations.dat.client import (
    DatClient,
    DatAuthenticationError,
    DatCredentials,
    MockDatProvider,
    build_dat_client,
)
from app.integrations.dat.mapper import map_dat_load_to_normalized
from app.seed.scenarios import STRATEGIC_LOAD_SCENARIOS


def _provider(**kwargs) -> MockDatProvider:
    kwargs.setdefault("service_account_email", "service@dat.example")
    kwargs.setdefault("service_account_password", "secret")
    kwargs.setdefault("user_email", "demo")
    return MockDatProvider(DatCredentials(**kwargs))


def _patch_dat_endpoints(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integrations.dat.client.settings.DAT_IDENTITY_BASE_URL",
        "https://identity.test",
    )
    monkeypatch.setattr(
        "app.integrations.dat.client.settings.DAT_FREIGHT_BASE_URL",
        "https://freight.test",
    )
    monkeypatch.setattr(
        "app.integrations.dat.client.settings.DAT_ORG_TOKEN_PATH",
        "/org-token",
    )
    monkeypatch.setattr(
        "app.integrations.dat.client.settings.DAT_USER_TOKEN_PATH",
        "/user-token",
    )
    monkeypatch.setattr(
        "app.integrations.dat.client.settings.DAT_LOAD_SEARCH_PATH",
        "/loads/search",
    )
    monkeypatch.setattr(
        "app.integrations.dat.client.settings.DAT_LOAD_SEARCH_RESULTS_PATH",
        "/loads/search/{search_id}/results",
    )


def test_mock_provider_postings_derive_from_scenarios():
    postings = _provider().search_loads()

    assert len(postings) == len(STRATEGIC_LOAD_SCENARIOS)
    assert {posting["id"] for posting in postings} == {
        f"MOCK-DAT-demo-{scenario.key}" for scenario in STRATEGIC_LOAD_SCENARIOS
    }
    assert all("rateUsd" in posting for posting in postings)
    assert all("rate" not in posting for posting in postings)


def test_mock_provider_results_are_tenant_specific():
    fleet_a = _provider(user_email="fleet-a@dat.example").search_loads()
    fleet_b = _provider(user_email="fleet-b@dat.example").search_loads()

    ids_a = {posting["id"] for posting in fleet_a}
    ids_b = {posting["id"] for posting in fleet_b}

    # Different tenants never receive the same listings.
    assert ids_a.isdisjoint(ids_b)
    assert all(pid.startswith("MOCK-DAT-fleet-a-dat-example-") for pid in ids_a)


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
    provider = MockDatProvider(
        DatCredentials(
            service_account_email="",
            service_account_password="",
            user_email="",
        )
    )

    with pytest.raises(DatAuthenticationError):
        provider.search_loads()


def test_live_client_authenticates_org_then_user_and_searches(monkeypatch):
    _patch_dat_endpoints(monkeypatch)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/org-token":
            return httpx.Response(
                200,
                json={"accessToken": "org-token", "expiresIn": 1800},
            )
        if request.url.path == "/user-token":
            assert request.headers["Authorization"] == "Bearer org-token"
            return httpx.Response(
                200,
                json={"accessToken": "user-token", "expiresIn": 1800},
            )
        if request.url.path == "/loads/search":
            assert request.headers["Authorization"] == "Bearer user-token"
            assert request.headers["x-dat-organization-token"] == "org-token"
            return httpx.Response(
                200,
                json={"searchId": "search-1", "status": "created"},
            )
        if request.url.path == "/loads/search/search-1/results":
            return httpx.Response(200, json={"loads": [{"id": "DAT-1"}]})
        return httpx.Response(404)

    client = DatClient(
        DatCredentials(
            service_account_email="service@dat.example",
            service_account_password="secret",
            user_email="user@dat.example",
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep_fn=lambda _: None,
    )

    loads = client.search_loads({"origin_state": "TX"})

    assert loads == [{"id": "DAT-1"}]
    assert [request.method for request in requests] == ["POST", "POST", "POST", "GET"]


def test_live_client_paginates_search_results(monkeypatch):
    _patch_dat_endpoints(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/org-token":
            return httpx.Response(200, json={"access_token": "org-token"})
        if request.url.path == "/user-token":
            return httpx.Response(200, json={"access_token": "user-token"})
        if request.url.path == "/loads/search":
            return httpx.Response(200, json={"search_id": "search-1"})
        if request.url.params.get("pageToken") == "next":
            return httpx.Response(200, json={"loads": [{"id": "DAT-2"}]})
        return httpx.Response(
            200,
            json={"loads": [{"id": "DAT-1"}], "nextPageToken": "next"},
        )

    client = DatClient(
        DatCredentials(
            service_account_email="service@dat.example",
            service_account_password="secret",
            user_email="user@dat.example",
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep_fn=lambda _: None,
    )

    assert client.search_loads() == [{"id": "DAT-1"}, {"id": "DAT-2"}]


def test_live_client_reauthenticates_after_unauthorized_search(monkeypatch):
    _patch_dat_endpoints(monkeypatch)
    auth_count = 0
    search_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal auth_count, search_count
        if request.url.path == "/org-token":
            auth_count += 1
            return httpx.Response(200, json={"access_token": f"org-{auth_count}"})
        if request.url.path == "/user-token":
            return httpx.Response(200, json={"access_token": f"user-{auth_count}"})
        if request.url.path == "/loads/search":
            search_count += 1
            if search_count == 1:
                return httpx.Response(401)
            return httpx.Response(200, json={"loads": [{"id": "DAT-1"}]})
        return httpx.Response(404)

    client = DatClient(
        DatCredentials(
            service_account_email="service@dat.example",
            service_account_password="secret",
            user_email="user@dat.example",
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert client.search_loads() == [{"id": "DAT-1"}]
    assert auth_count == 2


def test_build_dat_client_rejects_unknown_provider_mode():
    credentials = DatCredentials(
        service_account_email="service@dat.example",
        service_account_password="secret",
        user_email="user@dat.example",
    )

    with pytest.raises(ValueError):
        build_dat_client(credentials, mode="typo")
