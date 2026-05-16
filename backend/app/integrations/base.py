from abc import ABC, abstractmethod
from datetime import datetime

from app.schemas.driver import DriverCreate
from app.schemas.telemetry_event import TelemetryEventCreate
from app.schemas.truck import TruckCreate


class BaseProvider(ABC):
    """
    Contract every telematics provider must satisfy.

    Each subclass is responsible for both fetching raw data from its API
    and normalizing that data into internal Pydantic schemas.  The
    ingestion_service works exclusively through this interface and has no
    knowledge of any specific provider's API shape.

    Adding a new provider = subclass BaseProvider, implement all six methods.
    No other file needs to change.
    """

    provider_name: str  # set as a class attribute, e.g. "motive"

    # ------------------------------------------------------------------
    # Fetch — return raw dicts from the provider's API
    # ------------------------------------------------------------------

    @abstractmethod
    async def fetch_vehicles(self, since: datetime) -> list[dict]:
        """Return raw vehicle dicts updated at or after `since`."""

    @abstractmethod
    async def fetch_drivers(self, since: datetime) -> list[dict]:
        """Return raw driver/user dicts updated at or after `since`."""

    @abstractmethod
    async def fetch_locations(self, since: datetime) -> list[dict]:
        """Return raw vehicle-location dicts recorded at or after `since`."""

    # ------------------------------------------------------------------
    # Map — normalize provider raw dicts into internal schemas
    # Each returns (internal_schema, provider_id_str).
    # ------------------------------------------------------------------

    @abstractmethod
    def map_vehicle(self, raw: dict) -> tuple[TruckCreate, str]:
        """Normalize one raw vehicle dict into (TruckCreate, provider_id)."""

    @abstractmethod
    def map_driver(self, raw: dict) -> tuple[DriverCreate, str]:
        """Normalize one raw driver dict into (DriverCreate, provider_id)."""

    @abstractmethod
    def map_location(self, raw: dict, truck_id: str) -> tuple[TelemetryEventCreate, str]:
        """Normalize one raw location dict into (TelemetryEventCreate, provider_id)."""
