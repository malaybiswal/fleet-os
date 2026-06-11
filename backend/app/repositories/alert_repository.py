from datetime import datetime

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    def __init__(self):
        super().__init__(Alert)

    def create(self, db: Session, alert: Alert) -> Alert:
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def get_all(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        resolved: bool | None = None,
    ) -> list[Alert]:
        query = db.query(Alert)

        if resolved is not None:
            query = query.filter(Alert.resolved == resolved)

        return (
            query.order_by(Alert.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_all_by_fleet(
        self,
        db: Session,
        fleet_id: int,
        limit: int = 100,
        offset: int = 0,
        resolved: bool | None = None,
    ) -> list[Alert]:
        query = db.query(Alert).filter(Alert.fleet_id == fleet_id)

        if resolved is not None:
            query = query.filter(Alert.resolved == resolved)

        return (
            query.order_by(Alert.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_unresolved_by_fleet(self, db: Session, fleet_id: int) -> list[Alert]:
        return (
            db.query(Alert)
            .filter(
                Alert.fleet_id == fleet_id,
                Alert.resolved.is_(False),
            )
            .order_by(
                Alert.created_at.desc(),
                Alert.id.desc(),
            )
            .all()
        )

    def get_recent_alert_window(
        self,
        db: Session,
        fleet_id: int,
        start_time: datetime,
        end_time: datetime | None = None,
        truck_id: str | None = None,
        alert_type: str | None = None,
        resolved: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Alert]:
        query = db.query(Alert).filter(
            Alert.fleet_id == fleet_id,
            Alert.created_at >= start_time,
        )

        if end_time is not None:
            query = query.filter(Alert.created_at <= end_time)

        if truck_id is not None:
            query = query.filter(Alert.truck_id == truck_id)

        if alert_type is not None:
            query = query.filter(Alert.alert_type == alert_type)

        if resolved is not None:
            query = query.filter(Alert.resolved == resolved)

        return (
            query.order_by(
                Alert.created_at.desc(),
                Alert.id.desc(),
            )
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_id(self, db: Session, alert_id: int) -> Alert | None:
        return db.query(Alert).filter(Alert.id == alert_id).first()

    def resolve(self, db: Session, alert_id: int) -> Alert | None:
        alert = self.get_by_id(db, alert_id)
        if alert is None:
            return None

        alert.resolved = True
        db.commit()
        db.refresh(alert)
        return alert

    def exists_unresolved(
        self,
        db: Session,
        truck_id: str,
        alert_type: str,
    ) -> bool:
        return (
            db.query(Alert)
            .filter(
                Alert.truck_id == truck_id,
                Alert.alert_type == alert_type,
                Alert.resolved.is_(False),
            )
            .first()
            is not None
        )

    def get_open_count(self, db: Session) -> int:
        return db.query(Alert).filter(Alert.resolved.is_(False)).count()
