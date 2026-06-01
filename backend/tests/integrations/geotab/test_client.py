import pytest

from app.integrations.geotab.client import (
    AUTH_HOST,
    GeotabAPIError,
    GeotabClient,
    GeotabConfigError,
    GeotabCredentials,
    build_geotab_client,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class FakeHttpClient:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = []
        self.closed = False

    def post(self, url, json, headers):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return FakeResponse(self.payloads.pop(0))

    def close(self):
        self.closed = True


def test_fetch_device_status_info_authenticates_and_uses_returned_path():
    http_client = FakeHttpClient(
        [
            {
                "result": {
                    "credentials": {"sessionId": "session-1", "database": "Demo"},
                    "path": "demo.geotab.com",
                }
            },
            {"result": [{"device": {"id": "b1"}, "dateTime": "2026-01-01T00:00:00Z"}]},
        ]
    )
    client = GeotabClient(
        GeotabCredentials("Demo", "user@example.com", "secret"),
        http_client=http_client,
    )

    result = client.fetch_device_status_info()

    assert result == [{"device": {"id": "b1"}, "dateTime": "2026-01-01T00:00:00Z"}]
    assert http_client.calls[0]["url"] == f"https://{AUTH_HOST}/apiv1"
    assert http_client.calls[0]["json"]["method"] == "Authenticate"
    assert http_client.calls[1]["url"] == "https://demo.geotab.com/apiv1"
    assert http_client.calls[1]["json"]["params"]["typeName"] == "DeviceStatusInfo"


def test_fetch_device_status_info_reauthenticates_once_on_expired_session():
    http_client = FakeHttpClient(
        [
            {
                "result": {
                    "credentials": {"sessionId": "expired", "database": "Demo"},
                    "path": "ThisServer",
                }
            },
            {"error": {"name": "InvalidSessionException", "message": "expired"}},
            {
                "result": {
                    "credentials": {"sessionId": "fresh", "database": "Demo"},
                    "path": "ThisServer",
                }
            },
            {"result": [{"device": {"id": "b2"}, "dateTime": "2026-01-01T00:00:00Z"}]},
        ]
    )
    client = GeotabClient(
        GeotabCredentials("Demo", "user@example.com", "secret"),
        http_client=http_client,
    )

    result = client.fetch_device_status_info()

    assert len(result) == 1
    assert [call["json"]["method"] for call in http_client.calls] == [
        "Authenticate",
        "Get",
        "Authenticate",
        "Get",
    ]


def test_fetch_device_status_info_does_not_retry_non_session_errors():
    http_client = FakeHttpClient(
        [
            {
                "result": {
                    "credentials": {"sessionId": "session-1", "database": "Demo"},
                    "path": "ThisServer",
                }
            },
            {"error": {"name": "OtherException", "message": "bad request"}},
        ]
    )
    client = GeotabClient(
        GeotabCredentials("Demo", "user@example.com", "secret"),
        http_client=http_client,
    )

    with pytest.raises(GeotabAPIError):
        client.fetch_device_status_info()

    assert [call["json"]["method"] for call in http_client.calls] == [
        "Authenticate",
        "Get",
    ]


def test_build_geotab_client_reports_missing_config_without_secret_values():
    with pytest.raises(GeotabConfigError) as exc:
        build_geotab_client(
            database="Demo_fleet_os",
            username="user@example.com",
            password=None,
        )

    message = str(exc.value)
    assert "GEOTAB_PASSWORD" in message
    assert "Demo_fleet_os" not in message
    assert "user@example.com" not in message
