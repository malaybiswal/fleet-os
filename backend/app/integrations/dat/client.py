from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from time import sleep
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
    service_account_email: str
    service_account_password: str
    user_email: str
    base_url: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    provider_mode: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DatCredentials":
        return cls(
            service_account_email=str(payload.get("service_account_email") or ""),
            service_account_password=str(payload.get("service_account_password") or ""),
            user_email=str(payload.get("user_email") or ""),
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
        sleep_fn=sleep,
    ):
        self.credentials = credentials
        self.identity_base_url = settings.DAT_IDENTITY_BASE_URL.rstrip("/")
        self.freight_base_url = (
            base_url
            or credentials.base_url
            or settings.DAT_FREIGHT_BASE_URL
            or _default_freight_base_url()
        ).rstrip("/")
        self.http_client = http_client or httpx.Client(timeout=timeout_seconds)
        self._sleep = sleep_fn
        self._organization_token: str | None = None
        self._user_token: str | None = None
        self._expires_at: datetime | None = None

    def authenticate(self) -> None:
        if not (
            self.credentials.service_account_email
            and self.credentials.service_account_password
            and self.credentials.user_email
        ):
            raise DatAuthenticationError(
                "DAT live credentials require service account email, "
                "service account password, and user email"
            )

        response = self.http_client.post(
            self._identity_url(settings.DAT_ORG_TOKEN_PATH),
            json={
                "username": self.credentials.service_account_email,
                "password": self.credentials.service_account_password,
            },
        )
        if response.status_code in {401, 403}:
            raise DatAuthenticationError("DAT organization authentication failed")
        response.raise_for_status()
        org_payload = response.json()
        organization_token = _extract_token(org_payload)
        if not organization_token:
            raise DatAuthenticationError(
                "DAT organization authentication did not return a token"
            )

        response = self.http_client.post(
            self._identity_url(settings.DAT_USER_TOKEN_PATH),
            json={"username": self.credentials.user_email},
            headers={"Authorization": f"Bearer {organization_token}"},
        )
        if response.status_code in {401, 403}:
            raise DatAuthenticationError("DAT user authentication failed")
        response.raise_for_status()
        user_payload = response.json()
        user_token = _extract_token(user_payload)
        if not user_token:
            raise DatAuthenticationError("DAT user authentication did not return a token")

        expires_in = min(_extract_expires_in(org_payload), _extract_expires_in(user_payload))
        self._organization_token = organization_token
        self._user_token = user_token
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
        if self._organization_token is None or self._user_token is None:
            raise DatAuthenticationError("DAT client is not authenticated")

        response = self.http_client.post(
            self._freight_url(settings.DAT_LOAD_SEARCH_PATH),
            json=filters or {},
            headers=self._freight_headers(),
        )
        if response.status_code in {401, 403}:
            raise DatAuthenticationError("DAT session expired")
        response.raise_for_status()
        payload = response.json()
        direct_loads = _extract_loads(payload)
        if direct_loads is not None:
            return direct_loads

        search_id = _first_present(payload, "searchId", "search_id", "id")
        if not search_id:
            raise DatAPIError("DAT load search response did not include loads or a search id")

        return self._collect_search_results(str(search_id), filters or {})

    def _collect_search_results(
        self,
        search_id: str,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        loads: list[dict[str, Any]] = []
        next_page_token: str | None = None
        page = 1

        for _ in range(settings.DAT_SEARCH_POLL_ATTEMPTS):
            params: dict[str, Any] = {}
            if next_page_token:
                params["pageToken"] = next_page_token
            elif page > 1:
                params["page"] = page

            response = self.http_client.get(
                self._freight_url(
                    settings.DAT_LOAD_SEARCH_RESULTS_PATH.format(search_id=search_id)
                ),
                params={**filters, **params},
                headers=self._freight_headers(),
            )
            if response.status_code in {401, 403}:
                raise DatAuthenticationError("DAT session expired")
            response.raise_for_status()
            payload = response.json()

            status = str(_first_present(payload, "status", "state") or "").lower()
            if status in {"pending", "queued", "running", "processing"}:
                self._sleep(settings.DAT_SEARCH_POLL_INTERVAL_SECONDS)
                continue

            page_loads = _extract_loads(payload)
            if page_loads is None:
                raise DatAPIError("DAT load search results response was not a list")
            loads.extend(page_loads)

            next_page_token = _first_present(payload, "nextPageToken", "next_page_token")
            has_more = bool(_first_present(payload, "hasMore", "has_more"))
            total_pages = _first_present(payload, "totalPages", "total_pages")
            if next_page_token or has_more:
                page += 1
                continue
            if total_pages and page < int(total_pages):
                page += 1
                continue
            return loads

        raise DatAPIError("DAT load search results were not ready before polling timed out")

    def _token_expired(self) -> bool:
        return (
            self._organization_token is None
            or self._user_token is None
            or self._expires_at is None
            or datetime.now(timezone.utc) >= self._expires_at
        )

    def _identity_url(self, path: str) -> str:
        return f"{self.identity_base_url}/{path.lstrip('/')}"

    def _freight_url(self, path: str) -> str:
        return f"{self.freight_base_url}/{path.lstrip('/')}"

    def _freight_headers(self) -> dict[str, str]:
        if self._organization_token is None or self._user_token is None:
            raise DatAuthenticationError("DAT client is not authenticated")
        headers = {"Authorization": f"Bearer {self._user_token}"}
        org_header = settings.DAT_ORGANIZATION_TOKEN_HEADER.strip()
        if org_header:
            headers[org_header] = self._organization_token
        return headers


class MockDatProvider:
    def __init__(self, credentials: DatCredentials):
        self.credentials = credentials
        self.authenticated = False

    def authenticate(self) -> None:
        if not (
            self.credentials.service_account_email
            and self.credentials.service_account_password
            and self.credentials.user_email
        ):
            raise DatAuthenticationError(
                "Mock DAT credentials require service account email, password, and user email"
            )
        self.authenticated = True

    def search_loads(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not self.authenticated:
            self.authenticate()

        # Results are a deterministic function of this tenant's credentials and
        # their configured filters — mirroring how the live API scopes results to
        # the authenticated account. Postings are tenant-namespaced so two fleets
        # never receive the same listings, and saved filters narrow the set.
        tenant = _tenant_token(self.credentials.user_email)
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

    TODO: Once DAT's portal-gated posting schema is confirmed, replace any
    remaining generic field names here with the verified production names.
    """
    return {
        "id": f"MOCK-DAT-{tenant}-{scenario.key}",
        "origin": _split_place(scenario.origin),
        "destination": _split_place(scenario.destination),
        "equipment": scenario.equipment_type,
        "rateUsd": scenario.payout,
        "miles": scenario.loaded_miles,
        "deadheadMiles": scenario.deadhead_miles,
        "broker": {"name": scenario.broker_name},
    }


def _matches_filters(posting: dict[str, Any], filters: dict[str, Any]) -> bool:
    equipment = filters.get("equipment_type")
    if equipment and str(posting.get("equipment", "")).lower() != str(equipment).lower():
        return False

    origin_state = filters.get("origin_state")
    if origin_state and (posting.get("origin") or {}).get("state", "").upper() != str(
        origin_state
    ).upper():
        return False

    destination_state = filters.get("destination_state")
    if destination_state and (posting.get("destination") or {}).get(
        "state", ""
    ).upper() != str(destination_state).upper():
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
    if selected_mode != "live":
        raise ValueError("DAT_PROVIDER_MODE must be 'mock' or 'live'")
    return DatClient(credentials, http_client=http_client)


def _extract_token(payload: dict[str, Any]) -> str | None:
    value = _first_present(payload, "access_token", "accessToken", "token", "jwt")
    return str(value) if value else None


def _extract_expires_in(payload: dict[str, Any]) -> int:
    value = _first_present(payload, "expires_in", "expiresIn", "expirationSeconds")
    try:
        return int(value or 1800)
    except (TypeError, ValueError):
        return 1800


def _extract_loads(payload: Any) -> list[dict[str, Any]] | None:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return None
    for key in ("loads", "postings", "results", "items", "matches", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
        nested = _extract_loads(value)
        if nested is not None:
            return nested
    return None


def _first_present(payload: Any, *keys: str) -> Any:
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return None


def _default_freight_base_url() -> str:
    environment = settings.DAT_ENVIRONMENT.lower()
    if environment == "production":
        return "https://freight.api.dat.com"
    if environment == "staging":
        return "https://freight.api.staging.dat.com"
    raise ValueError("DAT_ENVIRONMENT must be 'staging' or 'production'")
