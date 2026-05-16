import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.config import settings
from app.integrations.base import BaseProvider
from app.integrations.providers.motive import mapper
from app.schemas.driver import DriverCreate
from app.schemas.telemetry_event import TelemetryEventCreate
from app.schemas.truck import TruckCreate

logger = logging.getLogger("fleet_os.motive")

_PER_PAGE = 25
# Refresh the access token 5 minutes before it actually expires (TTL is 2 hours).
_TOKEN_TTL_SECONDS = 7200
_TOKEN_REFRESH_BUFFER_SECONDS = 300


class MotiveClient(BaseProvider):
    """
    Motive (GoMotive) telematics API client — OAuth 2.0.

    API reference: https://developer-docs.gomotive.com
    Auth: Bearer token obtained via the OAuth 2.0 authorization code flow.
          The initial access token + refresh token must be placed in .env
          (MOTIVE_ACCESS_TOKEN / MOTIVE_REFRESH_TOKEN). This client will
          auto-refresh using the refresh token when the access token nears expiry.

    Pagination: page_no / per_page query params; stops when the returned page
                has fewer items than per_page.
    Rate limiting: on HTTP 429 we raise immediately; the scheduler retries
                   on the next cycle.
    """

    provider_name = "motive"

    def __init__(self) -> None:
        self._base_url = settings.MOTIVE_API_BASE_URL.rstrip("/")
        self._token_url = settings.MOTIVE_TOKEN_URL
        self._client_id = settings.MOTIVE_CLIENT_ID
        self._client_secret = settings.MOTIVE_CLIENT_SECRET
        self._access_token: str = settings.MOTIVE_ACCESS_TOKEN
        self._refresh_token: str = settings.MOTIVE_REFRESH_TOKEN
        # Track when the current access token was last refreshed so we can
        # proactively renew it before it expires.
        self._token_refreshed_at: datetime = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------

    async def fetch_vehicles(self, since: datetime) -> list[dict]:
        return await self._paginate(
            "/v2/vehicles",
            params={"updated_at[gte]": since.isoformat()},
            root_key="vehicles",
        )

    async def fetch_drivers(self, since: datetime) -> list[dict]:
        return await self._paginate(
            "/v2/users",
            params={"role": "driver", "updated_at[gte]": since.isoformat()},
            root_key="users",
        )

    async def fetch_locations(self, since: datetime) -> list[dict]:
        return await self._paginate(
            "/v2/vehicle_locations",
            params={"start_date": since.isoformat()},
            root_key="vehicle_locations",
        )

    # ------------------------------------------------------------------
    # Map (delegates to mapper.py — pure functions, no side effects)
    # ------------------------------------------------------------------

    def map_vehicle(self, raw: dict) -> tuple[TruckCreate, str]:
        return mapper.map_vehicle(raw)

    def map_driver(self, raw: dict) -> tuple[DriverCreate, str]:
        return mapper.map_driver(raw)

    def map_location(self, raw: dict, truck_id: str) -> tuple[TelemetryEventCreate, str]:
        return mapper.map_location(raw, truck_id)

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _is_token_expiring(self) -> bool:
        elapsed = (datetime.now(timezone.utc) - self._token_refreshed_at).total_seconds()
        return elapsed >= (_TOKEN_TTL_SECONDS - _TOKEN_REFRESH_BUFFER_SECONDS)

    async def _refresh_access_token(self, client: httpx.AsyncClient) -> None:
        if not self._refresh_token:
            raise RuntimeError(
                "MOTIVE_REFRESH_TOKEN is not set. Complete the OAuth authorization "
                "flow first and store the tokens in your .env file."
            )
        response = await client.post(
            self._token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        response.raise_for_status()
        token_data = response.json()
        self._access_token = token_data["access_token"]
        self._refresh_token = token_data.get("refresh_token", self._refresh_token)
        self._token_refreshed_at = datetime.now(timezone.utc)
        logger.info("Motive access token refreshed successfully")

    # ------------------------------------------------------------------
    # Pagination helper
    # ------------------------------------------------------------------

    async def _paginate(self, path: str, params: dict, root_key: str) -> list[dict]:
        results: list[dict] = []
        page = 1
        url = f"{self._base_url}{path}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            if self._is_token_expiring():
                await self._refresh_access_token(client)

            while True:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {self._access_token}"},
                    params={**params, "page_no": page, "per_page": _PER_PAGE},
                )

                if response.status_code == 401:
                    # Token may have expired mid-session; try one refresh and retry.
                    logger.warning("Motive 401 on %s — refreshing token and retrying", path)
                    await self._refresh_access_token(client)
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {self._access_token}"},
                        params={**params, "page_no": page, "per_page": _PER_PAGE},
                    )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "unknown")
                    raise RuntimeError(
                        f"Motive API rate limited on {path}; "
                        f"Retry-After: {retry_after}s. Will retry next cycle."
                    )

                response.raise_for_status()
                data = response.json()
                page_items: list[dict] = data.get(root_key, [])
                results.extend(page_items)

                logger.debug(
                    "Motive %s page %d: fetched %d records", path, page, len(page_items)
                )

                if len(page_items) < _PER_PAGE:
                    break
                page += 1

        return results
