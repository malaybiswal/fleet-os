import logging

from sqlalchemy.orm import Session

from app.models.fleet import Fleet
from app.seed.generators import build_fleet
from app.seed.mock_fleets import DEMO_FLEETS
from app.seed.types import FleetSeed

logger = logging.getLogger(__name__)


def get_or_create_demo_operations_fleet(db: Session) -> int:
    return _get_or_create_by_seed(db, DEMO_FLEETS[0])


def get_or_create_demo_refrigerated_fleet(db: Session) -> int:
    return _get_or_create_by_seed(db, DEMO_FLEETS[1])


def _get_or_create_by_seed(db: Session, fleet_seed: FleetSeed) -> int:
    fleet = db.query(Fleet).filter(Fleet.name == fleet_seed.name).one_or_none()
    if fleet is None:
        fleet = build_fleet(fleet_seed)
        db.add(fleet)
        db.flush()
        logger.info("Created demo fleet: %s (id=%s)", fleet.name, fleet.id)
    return fleet.id
