import logging
from hashlib import sha1
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.ingestion.normalized_events import NormalizedLoadObject
from app.models.load import Load
from app.schemas.load_evaluation import LoadEvaluationRequest
from app.services.load_evaluation_service import evaluate_load


logger = logging.getLogger(__name__)

MAX_LOAD_ID_LENGTH = 50
LOAD_ID_HASH_LENGTH = 12


class InvalidLoadError(ValueError):
    pass


class LoadIngestionService:
    def __init__(self, db: Session):
        self.db = db

    def ingest(self, obj: NormalizedLoadObject) -> Load:
        if obj.gross_revenue <= 0:
            raise InvalidLoadError("DAT load gross_revenue must be positive")
        if obj.total_miles <= 0:
            raise InvalidLoadError("DAT load total_miles must be positive")

        namespaced_load_id = _namespaced_load_id(obj)
        load = (
            self.db.query(Load)
            .filter(Load.load_id == namespaced_load_id, Load.fleet_id == obj.fleet_id)
            .first()
        )
        if load is None:
            load = Load(load_id=namespaced_load_id, fleet_id=obj.fleet_id)
            self.db.add(load)

        load.truck_id = None
        load.driver_id = None
        load.equipment_type = obj.equipment_type
        load.broker_name = obj.broker_name
        load.origin = obj.origin
        load.origin_lat = _decimal_or_none(obj.origin_lat)
        load.origin_lon = _decimal_or_none(obj.origin_lon)
        load.destination = obj.destination
        load.revenue = Decimal(str(obj.gross_revenue))
        load.miles = Decimal(str(obj.total_miles))
        load.deadhead_miles = Decimal(str(obj.deadhead_miles or 0))
        load.pickup_time = obj.pickup_time
        load.delivery_time = obj.delivery_time
        load.status = "available"
        load.source = obj.source
        load.external_ref = obj.source_event_id
        load.last_synced_at = datetime.now(timezone.utc)

        evaluation = evaluate_load(
            LoadEvaluationRequest(
                payout=float(load.revenue),
                loaded_miles=float(load.miles),
                deadhead_miles=float(load.deadhead_miles or 0),
                equipment_type=load.equipment_type or "Unknown",
                fuel_cost=_float_or_none(load.fuel_cost),
                maintenance_reserve=_float_or_none(load.maintenance_reserve),
                driver_cost=_float_or_none(load.driver_cost),
                tolls=_float_or_none(load.tolls),
            )
        )
        logger.info(
            "DAT load evaluated fleet_id=%s load_id=%s revenue_per_hour=%s recommendation=%s",
            obj.fleet_id,
            namespaced_load_id,
            evaluation.metrics.estimated_revenue_per_hour,
            evaluation.recommendation,
        )

        self.db.commit()
        self.db.refresh(load)
        return load


def _decimal_or_none(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _float_or_none(value) -> float | None:
    if value is None:
        return None
    return float(value)


def _namespaced_load_id(obj: NormalizedLoadObject) -> str:
    raw_load_id = f"{obj.source}:{obj.fleet_id}:{obj.source_event_id}"
    if len(raw_load_id) <= MAX_LOAD_ID_LENGTH:
        return raw_load_id

    digest = sha1(raw_load_id.encode("utf-8")).hexdigest()[:LOAD_ID_HASH_LENGTH]
    prefix_length = MAX_LOAD_ID_LENGTH - LOAD_ID_HASH_LENGTH - 1
    return f"{raw_load_id[:prefix_length]}:{digest}"
