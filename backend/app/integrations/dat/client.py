from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

import httpx

from app.config import settings


class DatAPIError(RuntimeError):
    pass


class DatAuthenticationError(DatAPIError):
    pass


@dataclass(frozen=True)
class DatCredentials:
    username: str
    password: str
    base_url: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    provider_mode: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DatCredentials":
        return cls(
            username=str(payload.get("username") or ""),
            password=str(payload.get("password") or ""),
            base_url=payload.get("base_url"),
            filters=payload.get("filters") or {},
            provider_mode=payload.get("provider_mode"),
        )


class DatProvider(Protocol):
    def authenticate(self) -> None:
        ...

    def search_loads(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        ...

    def close(self) -> None:
        ...


class DatClient:
    def __init__(
        self,
        credentials: DatCredentials,
        *,
        base_url: str | None = None,
        timeout_seconds: float = 30,
        http_client: httpx.Client | None = None,
    ):
        self.credentials = credentials
        self.base_url = (base_url or credentials.base_url or settings.DAT_BASE_URL).rstrip("/")
        self.http_client = http_client or httpx.Client(timeout=timeout_seconds)
        self._access_token: str | None = None
        self._expires_at: datetime | None = None

    def authenticate(self) -> None:
        response = self.http_client.post(
            f"{self.base_url}/oauth/token",
            json={
                "username": self.credentials.username,
                "password": self.credentials.password,
                "grant_type": "password",
            },
        )
        if response.status_code in {401, 403}:
            raise DatAuthenticationError("DAT authentication failed")
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise DatAuthenticationError("DAT authentication did not return an access token")

        expires_in = int(payload.get("expires_in") or 3600)
        self._access_token = str(token)
        self._expires_at = datetime.now(timezone.utc) + timedelta(seconds=max(1, expires_in - 30))

    def search_loads(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self._token_expired():
            self.authenticate()

        try:
            return self._search_loads(filters)
        except DatAuthenticationError:
            self.authenticate()
            return self._search_loads(filters)

    def close(self) -> None:
        self.http_client.close()

    def _search_loads(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self._access_token is None:
            raise DatAuthenticationError("DAT client is not authenticated")

        response = self.http_client.get(
            f"{self.base_url}/loads/search",
            params=filters or {},
            headers={"Authorization": f"Bearer {self._access_token}"},
        )
        if response.status_code in {401, 403}:
            raise DatAuthenticationError("DAT session expired")
        response.raise_for_status()
        payload = response.json()
        loads = payload.get("loads") if isinstance(payload, dict) else payload
        if not isinstance(loads, list):
            raise DatAPIError("DAT load search response was not a list")
        return loads

    def _token_expired(self) -> bool:
        return (
            self._access_token is None
            or self._expires_at is None
            or datetime.now(timezone.utc) >= self._expires_at
        )


class MockDatProvider:
    def __init__(self, credentials: DatCredentials):
        self.credentials = credentials
        self.authenticated = False

    def authenticate(self) -> None:
        if not self.credentials.username or not self.credentials.password:
            raise DatAuthenticationError("Mock DAT credentials require username and password")
        self.authenticated = True

    def search_loads(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not self.authenticated:
            self.authenticate()

        return [
            {
                "id": "MOCK-DAT-001",
                "origin": {"city": "Dallas", "state": "TX", "lat": 32.7767, "lon": -96.7970},
                "destination": {"city": "Houston", "state": "TX"},
                "equipment": "Dry Van",
                "rate": 1250,
                "miles": 245,
                "deadheadMiles": 20,
                "broker": {"name": "DAT Demo Brokerage"},
                "pickupTime": "2026-06-27T14:00:00Z",
                "deliveryTime": "2026-06-27T21:00:00Z",
                "weight": 36000,
                "commodity": "Consumer goods",
            },
            {
                "id": "MOCK-DAT-002",
                "origin": {"city": "Oklahoma City", "state": "OK", "lat": 35.4676, "lon": -97.5164},
                "destination": {"city": "Kansas City", "state": "MO"},
                "equipment": "Reefer",
                "rate": 2100,
                "miles": 355,
                "deadheadMiles": 55,
                "broker": {"name": "DAT Produce Desk"},
                "pickupTime": "2026-06-28T08:30:00Z",
                "deliveryTime": "2026-06-28T18:00:00Z",
                "weight": 41000,
                "commodity": "Fresh produce",
            },
        ]

    def close(self) -> None:
        return None


def build_dat_client(
    credentials: DatCredentials,
    *,
    mode: str | None = None,
    http_client: httpx.Client | None = None,
) -> DatProvider:
    selected_mode = (mode or credentials.provider_mode or settings.DAT_PROVIDER_MODE).lower()
    if selected_mode == "mock":
        return MockDatProvider(credentials)
    return DatClient(credentials, http_client=http_client)
