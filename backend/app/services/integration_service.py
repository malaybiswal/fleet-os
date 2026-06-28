import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.crypto import decrypt, encrypt
from app.integrations.dat.client import DatCredentials, build_dat_client
from app.integrations.truckstop.client import (
    TruckstopCredentials,
    build_truckstop_client,
)
from app.models.fleet_integration import FleetIntegration
from app.repositories.fleet_integration_repository import FleetIntegrationRepository


DAT_PROVIDER = "dat"
TRUCKSTOP_PROVIDER = "truckstop"
logger = logging.getLogger(__name__)


class IntegrationNotFoundError(ValueError):
    pass


class IntegrationService:
    def __init__(
        self,
        repository: FleetIntegrationRepository | None = None,
    ):
        self.repository = repository or FleetIntegrationRepository()

    def set_dat_credentials(
        self,
        db: Session,
        *,
        fleet_id: int,
        credentials: dict[str, Any],
    ) -> FleetIntegration:
        integration = self._set_provider_credentials(
            db,
            fleet_id=fleet_id,
            provider=DAT_PROVIDER,
            credentials=credentials,
        )
        logger.info("DAT integration connected fleet_id=%s", fleet_id)
        return integration

    def get_dat_status(
        self,
        db: Session,
        *,
        fleet_id: int,
    ) -> FleetIntegration | None:
        return self._get_provider_status(db, fleet_id=fleet_id, provider=DAT_PROVIDER)

    def decrypt_dat_credentials(self, integration: FleetIntegration) -> dict[str, Any]:
        return self._decrypt_provider_credentials(integration)

    def public_dat_config(self, integration: FleetIntegration) -> dict[str, Any]:
        """Non-secret saved config for display. Never includes the password.

        Fails soft: if decryption fails (e.g. key rotation), returns ``{}`` so the
        status endpoint degrades to "connected, config unavailable" instead of 500ing.
        """
        try:
            data = self.decrypt_dat_credentials(integration)
        except Exception:
            logger.exception(
                "Failed to decrypt DAT config fleet_id=%s", integration.fleet_id
            )
            return {}
        return {
            "service_account_email": data.get("service_account_email"),
            "user_email": data.get("user_email"),
            "base_url": data.get("base_url"),
            "filters": data.get("filters") or {},
        }

    def test_dat_connection(
        self,
        db: Session,
        *,
        fleet_id: int,
    ) -> bool:
        integration = self.get_dat_status(db, fleet_id=fleet_id)
        if integration is None or integration.status == "disabled":
            raise IntegrationNotFoundError("DAT integration is not connected")

        credentials = DatCredentials.from_dict(self.decrypt_dat_credentials(integration))
        client = build_dat_client(credentials)
        try:
            client.authenticate()
            return True
        finally:
            client.close()

    def disconnect_dat(
        self,
        db: Session,
        *,
        fleet_id: int,
    ) -> FleetIntegration:
        integration = self._disconnect_provider(
            db,
            fleet_id=fleet_id,
            provider=DAT_PROVIDER,
            provider_label="DAT",
        )
        logger.info("DAT integration disconnected fleet_id=%s", fleet_id)
        return integration

    def set_truckstop_credentials(
        self,
        db: Session,
        *,
        fleet_id: int,
        credentials: dict[str, Any],
    ) -> FleetIntegration:
        integration = self._set_provider_credentials(
            db,
            fleet_id=fleet_id,
            provider=TRUCKSTOP_PROVIDER,
            credentials=credentials,
        )
        logger.info("Truckstop integration connected fleet_id=%s", fleet_id)
        return integration

    def get_truckstop_status(
        self,
        db: Session,
        *,
        fleet_id: int,
    ) -> FleetIntegration | None:
        return self._get_provider_status(
            db,
            fleet_id=fleet_id,
            provider=TRUCKSTOP_PROVIDER,
        )

    def decrypt_truckstop_credentials(
        self,
        integration: FleetIntegration,
    ) -> dict[str, Any]:
        return self._decrypt_provider_credentials(integration)

    def public_truckstop_config(self, integration: FleetIntegration) -> dict[str, Any]:
        try:
            data = self.decrypt_truckstop_credentials(integration)
        except Exception:
            logger.exception(
                "Failed to decrypt Truckstop config fleet_id=%s",
                integration.fleet_id,
            )
            return {}
        return {
            "integration_id": data.get("integration_id"),
            "username": data.get("username"),
            "base_url": data.get("base_url"),
            "filters": data.get("filters") or {},
        }

    def test_truckstop_connection(
        self,
        db: Session,
        *,
        fleet_id: int,
    ) -> bool:
        integration = self.get_truckstop_status(db, fleet_id=fleet_id)
        if integration is None or integration.status == "disabled":
            raise IntegrationNotFoundError("Truckstop integration is not connected")

        credentials = TruckstopCredentials.from_dict(
            self.decrypt_truckstop_credentials(integration)
        )
        client = build_truckstop_client(credentials)
        try:
            client.authenticate()
            # Truckstop's SOAP API has no standalone token/ping step, so the
            # lightest call that actually exercises the credentials, endpoint, and
            # envelope is a one-result load search. Provider errors (auth or
            # otherwise) propagate to the router, which renders them to the user.
            client.search_loads({"page_size": 1})
            return True
        finally:
            client.close()

    def disconnect_truckstop(
        self,
        db: Session,
        *,
        fleet_id: int,
    ) -> FleetIntegration:
        integration = self._disconnect_provider(
            db,
            fleet_id=fleet_id,
            provider=TRUCKSTOP_PROVIDER,
            provider_label="Truckstop",
        )
        logger.info("Truckstop integration disconnected fleet_id=%s", fleet_id)
        return integration

    def _set_provider_credentials(
        self,
        db: Session,
        *,
        fleet_id: int,
        provider: str,
        credentials: dict[str, Any],
    ) -> FleetIntegration:
        encrypted_credentials = encrypt(json.dumps(credentials))
        return self.repository.upsert(
            db,
            fleet_id=fleet_id,
            provider=provider,
            encrypted_credentials=encrypted_credentials,
            status="connected",
            last_error=None,
        )

    def _get_provider_status(
        self,
        db: Session,
        *,
        fleet_id: int,
        provider: str,
    ) -> FleetIntegration | None:
        return self.repository.get_by_fleet_and_provider(
            db,
            fleet_id=fleet_id,
            provider=provider,
        )

    def _decrypt_provider_credentials(
        self,
        integration: FleetIntegration,
    ) -> dict[str, Any]:
        return json.loads(decrypt(integration.encrypted_credentials))

    def _disconnect_provider(
        self,
        db: Session,
        *,
        fleet_id: int,
        provider: str,
        provider_label: str,
    ) -> FleetIntegration:
        integration = self._get_provider_status(
            db,
            fleet_id=fleet_id,
            provider=provider,
        )
        if integration is None:
            raise IntegrationNotFoundError(
                f"{provider_label} integration is not connected"
            )

        integration.status = "disabled"
        integration.last_error = None
        db.commit()
        db.refresh(integration)
        return integration
