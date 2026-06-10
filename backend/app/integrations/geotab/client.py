from dataclasses import dataclass
from typing import Any

import httpx


AUTH_HOST = "my.geotab.com"
API_PATH = "/apiv1"
SESSION_EXPIRED_ERROR_NAMES = {
    "DbUnavailableException",
    "InvalidUserException",
    "SecurityException",
    "InvalidSessionException",
}


class GeotabConfigError(RuntimeError):
    pass


class GeotabAPIError(RuntimeError):
    def __init__(self, error: dict[str, Any]):
        self.error = error
        self.name = str(error.get("name") or error.get("code") or "")
        message = error.get("message") or "Geotab API request failed"
        super().__init__(str(message))


@dataclass(frozen=True)
class GeotabCredentials:
    database: str
    username: str
    password: str


class GeotabClient:
    def __init__(
        self,
        credentials: GeotabCredentials,
        *,
        timeout_seconds: float = 30,
        http_client: httpx.Client | None = None,
    ):
        self.credentials = credentials
        self.timeout_seconds = timeout_seconds
        self.http_client = http_client or httpx.Client(timeout=timeout_seconds)
        self._geotab_credentials: dict[str, Any] | None = None
        self._data_host = AUTH_HOST

    def authenticate(self) -> None:
        response = self._call(
            host=AUTH_HOST,
            method="Authenticate",
            params={
                "database": self.credentials.database,
                "userName": self.credentials.username,
                "password": self.credentials.password,
            },
        )

        result = response["result"]
        self._geotab_credentials = result["credentials"]
        self._data_host = _resolve_data_host(result.get("path"))

    def fetch_device_status_info(self) -> list[dict[str, Any]]:
        if self._geotab_credentials is None:
            self.authenticate()

        try:
            response = self._fetch_device_status_info()
        except GeotabAPIError as exc:
            if not _is_session_expired(exc):
                raise

            self.authenticate()
            response = self._fetch_device_status_info()

        result = response.get("result", [])
        if not isinstance(result, list):
            raise GeotabAPIError(
                {
                    "name": "UnexpectedResult",
                    "message": "Geotab DeviceStatusInfo response result was not a list",
                }
            )

        return result

    def close(self) -> None:
        self.http_client.close()

    def _fetch_device_status_info(self) -> dict[str, Any]:
        if self._geotab_credentials is None:
            raise GeotabConfigError("Geotab client is not authenticated")

        return self._call(
            host=self._data_host,
            method="Get",
            params={
                "typeName": "DeviceStatusInfo",
                "credentials": self._geotab_credentials,
            },
        )

    def _call(
        self,
        *,
        host: str,
        method: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        response = self.http_client.post(
            f"https://{host}{API_PATH}",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params,
            },
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        rpc_response = response.json()

        if "error" in rpc_response:
            raise GeotabAPIError(rpc_response["error"])

        return rpc_response


def build_geotab_client(
    *,
    database: str | None,
    username: str | None,
    password: str | None,
) -> GeotabClient:
    missing = [
        name
        for name, value in (
            ("GEOTAB_DATABASE", database),
            ("GEOTAB_USERNAME", username),
            ("GEOTAB_PASSWORD", password),
        )
        if not value
    ]

    if missing:
        raise GeotabConfigError(
            f"Missing required Geotab environment variables: {', '.join(missing)}"
        )

    return GeotabClient(
        GeotabCredentials(
            database=database,
            username=username,
            password=password,
        )
    )


def _resolve_data_host(path: str | None) -> str:
    if path in (None, "", "ThisServer"):
        return AUTH_HOST
    return path


def _is_session_expired(error: GeotabAPIError) -> bool:
    return error.name in SESSION_EXPIRED_ERROR_NAMES
