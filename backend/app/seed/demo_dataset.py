from datetime import datetime, timezone
import random

from app.seed.mock_alerts import build_demo_alerts
from app.seed.mock_facilities import build_demo_dwell_events
from app.seed.mock_fleets import (
    DEFAULT_BASE_DATE,
    DEFAULT_DEMO_SEED,
    DEMO_FLEETS,
    DEMO_FLEET_NAMES,
    DEMO_ID_PREFIX,
)
from app.seed.mock_loads import build_demo_loads
from app.seed.mock_trucks import DEMO_DRIVERS, build_demo_trucks_from_latest_telemetry
from app.seed.types import DemoSeedDataset
from app.simulator.telemetry import build_demo_telemetry_events


def build_demo_dataset(
    seed: int = DEFAULT_DEMO_SEED,
    base_date: datetime = DEFAULT_BASE_DATE,
) -> DemoSeedDataset:
    rng = random.Random(seed)
    base_date = _ensure_utc(base_date)
    telemetry_events = build_demo_telemetry_events(base_date, rng)

    return DemoSeedDataset(
        seed=seed,
        base_date=base_date,
        fleets=DEMO_FLEETS,
        drivers=DEMO_DRIVERS,
        trucks=build_demo_trucks_from_latest_telemetry(telemetry_events),
        loads=build_demo_loads(base_date, rng),
        dwell_events=build_demo_dwell_events(base_date, rng),
        telemetry_events=telemetry_events,
        alerts=build_demo_alerts(base_date),
    )


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
