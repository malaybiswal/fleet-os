from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

import httpx

from app.config import settings
from app.seed.scenarios import STRATEGIC_LOAD_SCENARIOS, LoadScenario


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

        # Results are a deterministic function of this tenant's credentials and
        # their configured filters — mirroring how the live API scopes results to
        # the authenticated account. Postings are tenant-namespaced so two fleets
        # never receive the same listings, and saved filters narrow the set.
        tenant = _tenant_token(self.credentials.username)
        effective_filters = {**(self.credentials.filters or {}), **(filters or {})}
        postings = [
            _scenario_to_dat_posting(scenario, tenant)
            for scenario in STRATEGIC_LOAD_SCENARIOS
        ]
        return [posting for posting in postings if _matches_filters(posting, effective_filters)]

    def close(self) -> None:
        return None


def _tenant_token(username: str | None) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (username or "anon").lower()).strip("-")
    return slug or "anon"


def _scenario_to_dat_posting(scenario: LoadScenario, tenant: str) -> dict[str, Any]:
    """Render a strategic load scenario as a raw DAT posting for ``tenant``.

    Keeping the mock provider sourced from the same scenario definitions as the
    scripted demo seed means a mock DAT sync tells the same story and stays
    consistent if the scenarios change. The id is tenant-namespaced so different
    fleets receive distinct postings. The shape matches what
    ``app.integrations.dat.mapper.map_dat_load_to_normalized`` expects.
    """
    return {
        "id": f"MOCK-DAT-{tenant}-{scenario.key}",
        "origin": _split_place(scenario.origin),
        "destination": _split_place(scenario.destination),
        "equipment": scenario.equipment_type,
        "rate": scenario.payout,
        "miles": scenario.loaded_miles,
        "deadheadMiles": scenario.deadhead_miles,
        "broker": {"name": scenario.broker_name},
    }


def _matches_filters(posting: dict[str, Any], filters: dict[str, Any]) -> bool:
    equipment = filters.get("equipment_type")
    if equipment and str(posting.get("equipment", "")).lower() != str(equipment).lower():
        return False

    origin_state = filters.get("origin_state")
    if origin_state and (posting.get("origin") or {}).get("state", "").upper() != str(origin_state).upper():
        return False

    destination_state = filters.get("destination_state")
    if destination_state and (posting.get("destination") or {}).get("state", "").upper() != str(destination_state).upper():
        return False

    return True


def _split_place(place: str) -> dict[str, str]:
    """Split a ``"City, ST"`` scenario string into the dict shape the mapper expects."""
    city, _, state = place.partition(",")
    parsed = {"city": city.strip()}
    if state.strip():
        parsed["state"] = state.strip()
    return parsed


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
