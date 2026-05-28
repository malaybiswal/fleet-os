from datetime import datetime, timezone

from app.seed.types import FleetSeed

DEFAULT_DEMO_SEED = 32032
DEFAULT_BASE_DATE = datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc)
DEMO_ID_PREFIX = "DEMO-"
DEMO_FLEET_NAMES = ("Demo Fleet - Operations", "Demo Fleet - Refrigerated")

DEMO_FLEETS: tuple[FleetSeed, ...] = (
    FleetSeed(key="operations", name=DEMO_FLEET_NAMES[0]),
    FleetSeed(key="refrigerated", name=DEMO_FLEET_NAMES[1]),
)
