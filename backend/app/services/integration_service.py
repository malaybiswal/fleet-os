import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.crypto import decrypt, encrypt
from app.integrations.dat.client import DatCredentials, build_dat_client
from app.models.fleet_integration import FleetIntegration
from app.repositories.fleet_integration_repository import FleetIntegrationRepository


DAT_PROVIDER = "dat"
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
        encrypted_credentials = encrypt(json.dumps(credentials))
        integration = self.repository.upsert(
            db,
            fleet_id=fleet_id,
            provider=DAT_PROVIDER,
            encrypted_credentials=encrypted_credentials,
            status="connected",
            last_error=None,
        )
        logger.info("DAT integration connected fleet_id=%s", fleet_id)
        return integration

    def get_dat_status(
        self,
        db: Session,
        *,
        fleet_id: int,
    ) -> FleetIntegration | None:
        return self.repository.get_by_fleet_and_provider(
            db,
            fleet_id=fleet_id,
            provider=DAT_PROVIDER,
        )

    def decrypt_dat_credentials(self, integration: FleetIntegration) -> dict[str, Any]:
        return json.loads(decrypt(integration.encrypted_credentials))

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
            "username": data.get("username"),
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
        integration = self.get_dat_status(db, fleet_id=fleet_id)
        if integration is None:
            raise IntegrationNotFoundError("DAT integration is not connected")

        integration.status = "disabled"
        integration.last_error = None
        db.commit()
        db.refresh(integration)
        logger.info("DAT integration disconnected fleet_id=%s", fleet_id)
        return integration
