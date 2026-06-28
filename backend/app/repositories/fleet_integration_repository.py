from datetime import datetime

from sqlalchemy.orm import Session

from app.models.fleet_integration import FleetIntegration
from app.repositories.base import BaseRepository


class FleetIntegrationRepository(BaseRepository[FleetIntegration]):
    def __init__(self):
        super().__init__(FleetIntegration)

    def get_by_fleet_and_provider(
        self,
        db: Session,
        *,
        fleet_id: int,
        provider: str,
    ) -> FleetIntegration | None:
        return (
            db.query(FleetIntegration)
            .filter(
                FleetIntegration.fleet_id == fleet_id,
                FleetIntegration.provider == provider,
            )
            .first()
        )

    def upsert(
        self,
        db: Session,
        *,
        fleet_id: int,
        provider: str,
        encrypted_credentials: str,
        status: str = "connected",
        last_error: str | None = None,
    ) -> FleetIntegration:
        integration = self.get_by_fleet_and_provider(
            db,
            fleet_id=fleet_id,
            provider=provider,
        )
        if integration is None:
            integration = FleetIntegration(
                fleet_id=fleet_id,
                provider=provider,
                encrypted_credentials=encrypted_credentials,
                status=status,
                last_error=last_error,
            )
            db.add(integration)
        else:
            integration.encrypted_credentials = encrypted_credentials
            integration.status = status
            integration.last_error = last_error

        db.commit()
        db.refresh(integration)
        return integration

    def list_connected_by_provider(
        self,
        db: Session,
        *,
        provider: str,
    ) -> list[FleetIntegration]:
        return (
            db.query(FleetIntegration)
            .filter(
                FleetIntegration.provider == provider,
                FleetIntegration.status.in_(("connected", "error")),
            )
            .order_by(FleetIntegration.fleet_id.asc())
            .all()
        )

    def update_sync_status(
        self,
        db: Session,
        *,
        integration: FleetIntegration,
        status: str | None = None,
        last_sync_at: datetime | None = None,
        last_error: str | None = None,
    ) -> FleetIntegration:
        if status is not None:
            integration.status = status
        integration.last_sync_at = last_sync_at
        integration.last_error = last_error
        db.commit()
        db.refresh(integration)
        return integration
