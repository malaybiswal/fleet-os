import xml.etree.ElementTree as ET

import httpx
import pytest

from app.integrations.truckstop.client import (
    MockTruckstopProvider,
    TruckstopAuthenticationError,
    TruckstopClient,
    TruckstopCredentials,
    _criteria_from_filters,
    build_truckstop_client,
)
from app.integrations.truckstop.mapper import map_truckstop_load_to_normalized
from app.seed.scenarios import STRATEGIC_LOAD_SCENARIOS


def _provider(**kwargs) -> MockTruckstopProvider:
    kwargs.setdefault("integration_id", "12345")
    kwargs.setdefault("username", "demo")
    kwargs.setdefault("password", "secret")
    return MockTruckstopProvider(TruckstopCredentials(**kwargs))


def _patch_truckstop_endpoints(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integrations.truckstop.client.settings.TRUCKSTOP_LOADSEARCH_BASE_URL",
        "https://truckstop.test",
    )
    monkeypatch.setattr(
        "app.integrations.truckstop.client.settings.TRUCKSTOP_LOADSEARCH_PATH",
        "/v13/Searching/LoadSearch.svc",
    )
    monkeypatch.setattr(
        "app.integrations.truckstop.client.settings.TRUCKSTOP_LOADSEARCH_SOAP_ACTION",
        "http://webservices.truckstop.com/v12/ILoadSearch/GetLoadSearchResults",
    )


def test_mock_provider_postings_derive_from_scenarios():
    postings = _provider().search_loads()

    assert len(postings) == len(STRATEGIC_LOAD_SCENARIOS)
    assert {posting["ID"] for posting in postings} == {
        f"MOCK-TRUCKSTOP-demo-{scenario.key}"
        for scenario in STRATEGIC_LOAD_SCENARIOS
    }
    assert all("Payment" in posting for posting in postings)
    assert all("OriginCity" in posting for posting in postings)


def test_mock_provider_results_are_tenant_specific():
    fleet_a = _provider(username="fleet-a").search_loads()
    fleet_b = _provider(username="fleet-b").search_loads()

    ids_a = {posting["ID"] for posting in fleet_a}
    ids_b = {posting["ID"] for posting in fleet_b}

    assert ids_a.isdisjoint(ids_b)
    assert all(pid.startswith("MOCK-TRUCKSTOP-fleet-a-") for pid in ids_a)


def test_mock_provider_honors_equipment_filter():
    postings = _provider(filters={"equipment_type": "Reefer"}).search_loads()

    assert postings
    assert all(posting["Equipment"] == "R" for posting in postings)
    assert len(postings) < len(STRATEGIC_LOAD_SCENARIOS)


def test_mock_provider_call_filters_override_saved_filters():
    provider = _provider(filters={"equipment_type": "Reefer"})

    postings = provider.search_loads({"equipment_type": "Flatbed"})

    assert postings
    assert all(posting["Equipment"] == "F" for posting in postings)


def test_mock_provider_postings_round_trip_through_mapper():
    for posting in _provider().search_loads():
        normalized = map_truckstop_load_to_normalized(posting, fleet_id=8)

        assert normalized.source == "truckstop"
        assert normalized.gross_revenue > 0
        assert normalized.total_miles > 0
        assert normalized.origin
        assert normalized.destination


def test_mock_provider_requires_credentials():
    provider = MockTruckstopProvider(
        TruckstopCredentials(
            integration_id="",
            username="",
            password="",
        )
    )

    with pytest.raises(TruckstopAuthenticationError):
        provider.search_loads()


def test_live_client_builds_soap_envelope_and_parses_results(monkeypatch):
    _patch_truckstop_endpoints(monkeypatch)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body = request.content.decode()
        assert request.url.path == "/v13/Searching/LoadSearch.svc"
        assert request.headers["SOAPAction"].endswith("/GetLoadSearchResults")
        assert "<web:IntegrationId>12345</web:IntegrationId>" in body
        assert "<web:UserName>truckstop-user</web:UserName>" in body
        assert "<web1:OriginState>TX</web1:OriginState>" in body
        return httpx.Response(
            200,
            content="""
            <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
              <s:Body>
                <GetLoadSearchResultsResponse xmlns="http://webservices.truckstop.com/v12">
                  <GetLoadSearchResultsResult xmlns:a="http://schemas.datacontract.org/2004/07/WebServices.Objects">
                    <a:SearchResults>
                      <a:LoadSearchItem>
                        <a:ID>6483304</a:ID>
                        <a:OriginCity>Vandalia</a:OriginCity>
                        <a:OriginState>IL</a:OriginState>
                        <a:DestinationCity>Houston</a:DestinationCity>
                        <a:DestinationState>TX</a:DestinationState>
                        <a:Equipment>V</a:Equipment>
                        <a:Payment>800.00</a:Payment>
                        <a:Miles>860</a:Miles>
                        <a:CompanyName>Reliable</a:CompanyName>
                      </a:LoadSearchItem>
                    </a:SearchResults>
                  </GetLoadSearchResultsResult>
                </GetLoadSearchResultsResponse>
              </s:Body>
            </s:Envelope>
            """,
        )

    client = TruckstopClient(
        TruckstopCredentials(
            integration_id="12345",
            username="truckstop-user",
            password="secret",
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    loads = client.search_loads({"origin_state": "TX", "equipment_type": "Dry Van"})

    assert loads == [
        {
            "ID": "6483304",
            "OriginCity": "Vandalia",
            "OriginState": "IL",
            "DestinationCity": "Houston",
            "DestinationState": "TX",
            "Equipment": "V",
            "Payment": "800.00",
            "Miles": "860",
            "CompanyName": "Reliable",
        }
    ]
    assert [request.method for request in requests] == ["POST"]


def test_build_truckstop_client_rejects_unknown_provider_mode():
    credentials = TruckstopCredentials(
        integration_id="12345",
        username="user",
        password="secret",
    )

    with pytest.raises(ValueError):
        build_truckstop_client(credentials, mode="typo")


def test_criteria_clamps_ranges_and_page_size():
    criteria = _criteria_from_filters(
        {"origin_range": 10, "destination_range": 999, "page_size": 5000}
    )

    assert criteria["OriginRange"] == 25
    assert criteria["DestinationRange"] == 300
    assert criteria["PageSize"] == 200


def test_criteria_normalizes_invalid_load_type_and_sort_defaults():
    criteria = _criteria_from_filters({"load_type": "bogus"})

    assert criteria["LoadType"] == "Full"
    assert criteria["SortBy"] == "Age"
    # Newest-first by default: Age ascending.
    assert criteria["SortDescending"] == "false"


def test_criteria_honors_valid_load_type_and_sort_overrides():
    criteria = _criteria_from_filters(
        {"load_type": "partial", "sort_by": "payment", "sort_descending": True}
    )

    assert criteria["LoadType"] == "Partial"
    assert criteria["SortBy"] == "Payment"
    assert criteria["SortDescending"] == "true"


def test_criteria_caps_equipment_to_three_codes():
    criteria = _criteria_from_filters(
        {"equipment_type": "Dry Van, Reefer, Flatbed, Power Only"}
    )

    assert criteria["EquipmentType"] == "V,R,F"


def test_search_envelope_includes_sort_by_in_order_and_is_well_formed():
    client = TruckstopClient(
        TruckstopCredentials(integration_id="12345", username="u", password="p"),
        base_url="https://truckstop.test",
    )

    envelope = client._build_search_envelope({"origin_state": "TX"})

    # Must be parseable XML (well-formed envelope).
    ET.fromstring(envelope)
    assert "<web1:SortBy>Age</web1:SortBy>" in envelope
    # WCF DataContract ordering: SortBy must precede SortDescending.
    assert envelope.index("<web1:SortBy>") < envelope.index("<web1:SortDescending>")
    assert "<web1:OriginState>TX</web1:OriginState>" in envelope


def test_search_loads_raises_authentication_error_on_soap_fault():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=(
                '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">'
                "<s:Body><s:Fault><faultstring>Invalid credentials supplied"
                "</faultstring></s:Fault></s:Body></s:Envelope>"
            ),
        )

    client = TruckstopClient(
        TruckstopCredentials(integration_id="12345", username="u", password="bad"),
        base_url="https://truckstop.test",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(TruckstopAuthenticationError):
        client.search_loads({"page_size": 1})


def test_search_loads_raises_authentication_error_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, content="<unauthorized/>")

    client = TruckstopClient(
        TruckstopCredentials(integration_id="12345", username="u", password="bad"),
        base_url="https://truckstop.test",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(TruckstopAuthenticationError):
        client.search_loads({"page_size": 1})
