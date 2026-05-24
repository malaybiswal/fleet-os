from datetime import date

import httpx
import pytest

from app.importers import fmcsa_carriers
from app.importers.fmcsa_carriers import (
    MalformedCarrierRecord,
    _format_phone,
    fetch_socrata_page,
    transform_company_census_record,
)


def representative_record(**overrides):
    record = {
        "dot_number": "283913",
        "legal_name": "MORRELLE TRANSFER INC",
        "dba_name": "MORRELLE",
        "phone": "9204678300",
        "email_address": "morrelletransfer@sbcglobal.net",
        "phy_street": "801 FOREST AVE",
        "phy_city": "SHEBOYGAN FLS",
        "phy_state": "WI",
        "phy_zip": "53085-2527",
        "phy_country": "US",
        "status_code": "A",
        "add_date": "19861216",
        "power_units": "5",
        "total_drivers": "7",
        "docket1prefix": "MC",
        "docket1": "189139",
        "crgo_genfreight": "X",
        "crgo_machlrg": "X",
    }
    record.update(overrides)
    return record


# Tests the normal FMCSA census-row transform path, including identifiers,
# contact fields, authority metadata, fleet counts, and cargo flags.
def test_transform_maps_representative_record():
    carrier = transform_company_census_record(representative_record())

    assert carrier.dot_number == "283913"
    assert carrier.mc_number == "MC189139"
    assert carrier.legal_name == "MORRELLE TRANSFER INC"
    assert carrier.phone == "(920) 467-8300"
    assert carrier.email == "morrelletransfer@sbcglobal.net"
    assert carrier.address_line1 == "801 FOREST AVE"
    assert carrier.state == "WI"
    assert carrier.authority_status == "active"
    assert carrier.authority_date == date(1986, 12, 16)
    assert carrier.power_units == 5
    assert carrier.driver_count == 7
    assert carrier.cargo_types == ["general_freight", "machinery_large_objects"]


# Tests each supported FMCSA authority status code maps to the backend enum value.
@pytest.mark.parametrize(
    ("status_code", "expected"),
    [("A", "active"), ("I", "inactive"), ("P", "pending")],
)
def test_transform_maps_known_status_codes(status_code, expected):
    carrier = transform_company_census_record(
        representative_record(status_code=status_code)
    )

    assert carrier.authority_status == expected


# Tests that an unexpected authority status code is preserved in lowercase and logged.
def test_transform_preserves_unknown_status_code_with_warning(caplog):
    carrier = transform_company_census_record(representative_record(status_code="Z"))

    assert carrier.authority_status == "z"
    assert "Unexpected FMCSA authority status code" in caplog.text


# Tests that blank or missing optional FMCSA fields do not create empty strings/lists.
def test_transform_sets_sparse_optional_fields_to_none():
    carrier = transform_company_census_record(
        representative_record(
            dba_name=" ",
            email_address=None,
            docket1prefix=None,
            docket1=None,
            crgo_genfreight=None,
            crgo_machlrg=None,
        )
    )

    assert carrier.dba_name is None
    assert carrier.email is None
    assert carrier.mc_number is None
    assert carrier.cargo_types is None


# Tests that records missing required carrier identity fields are rejected as malformed.
@pytest.mark.parametrize("missing_field", ["dot_number", "legal_name"])
def test_transform_rejects_records_missing_required_fields(missing_field):
    record = representative_record()
    record.pop(missing_field)

    with pytest.raises(MalformedCarrierRecord):
        transform_company_census_record(record)


# Tests that Socrata fetches include pagination, filters, and the app token header.
def test_fetch_sends_pagination_params_and_app_token(monkeypatch):
    captured_request = {}

    def handler(request):
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-App-Token")
        return httpx.Response(200, json=[{"dot_number": "1"}])

    monkeypatch.setattr(fmcsa_carriers.settings, "SOCRATA_APP_TOKEN", "token-123")
    client = httpx.Client(transport=httpx.MockTransport(handler))

    records = fetch_socrata_page(
        limit=25,
        offset=50,
        filters={"$where": "phy_state='TX'"},
        url="https://example.test/resource.json",
        client=client,
    )

    assert records == [{"dot_number": "1"}]
    assert "%24limit=25" in captured_request["url"]
    assert "%24offset=50" in captured_request["url"]
    assert "phy_state%3D%27TX%27" in captured_request["url"]
    assert captured_request["token"] == "token-123"


# Tests that Socrata fetches omit the app token header when no token is configured.
def test_fetch_does_not_send_app_token_when_absent(monkeypatch):
    captured_headers = {}

    def handler(request):
        captured_headers.update(request.headers)
        return httpx.Response(200, json=[])

    monkeypatch.setattr(fmcsa_carriers.settings, "SOCRATA_APP_TOKEN", None)
    client = httpx.Client(transport=httpx.MockTransport(handler))

    fetch_socrata_page(
        limit=1,
        offset=0,
        url="https://example.test/resource.json",
        client=client,
    )

    assert "X-App-Token" not in captured_headers


# Tests that transient Socrata server errors are retried before returning records.
def test_fetch_retries_transient_server_errors(monkeypatch):
    responses = [httpx.Response(500), httpx.Response(200, json=[{"dot_number": "1"}])]
    monkeypatch.setattr(fmcsa_carriers, "_sleep_before_retry", lambda attempt: None)

    def handler(request):
        return responses.pop(0)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    records = fetch_socrata_page(
        limit=1,
        offset=0,
        url="https://example.test/resource.json",
        client=client,
    )

    assert records == [{"dot_number": "1"}]
    assert responses == []


# Tests that non-retryable Socrata client errors surface as HTTPStatusError.
def test_fetch_raises_on_client_errors():
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(400))
    )

    with pytest.raises(httpx.HTTPStatusError):
        fetch_socrata_page(
            limit=1,
            offset=0,
            url="https://example.test/resource.json",
            client=client,
        )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("9204678300", "(920) 467-8300"),
        ("19204678300", "(920) 467-8300"),
        (None, None),
        ("  ", None),
        ("123", "123"),
    ],
)
def test_format_phone(raw, expected):
    assert _format_phone(raw) == expected
