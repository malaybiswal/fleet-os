from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
import random


TELEMETRY_INTERVAL_MINUTES = 5
DEMO_TELEMETRY_EVENT_COUNTS = {
    "DEMO-TRUCK-001": 49,
    "DEMO-TRUCK-002": 37,
    "DEMO-TRUCK-003": 85,
    "DEMO-TRUCK-004": 49,
    "DEMO-TRUCK-005": 49,
    "DEMO-TRUCK-006": 49,
    "DEMO-TRUCK-007": 5,
}
DEMO_TELEMETRY_EVENT_TOTAL = sum(DEMO_TELEMETRY_EVENT_COUNTS.values())


@dataclass(frozen=True)
class TelemetryEventSeed:
    truck_id: str
    fleet_key: str
    timestamp: datetime
    latitude: Decimal
    longitude: Decimal
    speed: Decimal
    heading: int
    reported_status: str
    location_description: str
    rpm: int
    engine_temp: Decimal
    fuel_level: Decimal
    idle_minutes: int
    reefer_temp: Decimal
    load_weight: Decimal


@dataclass(frozen=True)
class TelemetryTimelineSpec:
    truck_id: str
    fleet_key: str
    scenario: str
    location_description: str
    start_latitude: Decimal
    start_longitude: Decimal
    end_latitude: Decimal
    end_longitude: Decimal
    event_count: int
    speed_mph: Decimal
    heading: int
    start_offset_minutes: int
    rpm: int
    engine_temp: Decimal
    fuel_level: Decimal
    idle_minutes: int
    reefer_temp: Decimal
    load_weight: Decimal


DEMO_TELEMETRY_TIMELINES: tuple[TelemetryTimelineSpec, ...] = (
    TelemetryTimelineSpec(
        truck_id="DEMO-TRUCK-001",
        fleet_key="operations",
        scenario="moving",
        location_description="Dallas to Houston",
        start_latitude=Decimal("32.776700"),
        start_longitude=Decimal("-96.797000"),
        end_latitude=Decimal("29.760400"),
        end_longitude=Decimal("-95.369800"),
        event_count=DEMO_TELEMETRY_EVENT_COUNTS["DEMO-TRUCK-001"],
        speed_mph=Decimal("67"),
        heading=158,
        start_offset_minutes=0,
        rpm=1480,
        engine_temp=Decimal("184"),
        fuel_level=Decimal("78"),
        idle_minutes=0,
        reefer_temp=Decimal("37"),
        load_weight=Decimal("24200"),
    ),
    TelemetryTimelineSpec(
        truck_id="DEMO-TRUCK-002",
        fleet_key="operations",
        scenario="slow",
        location_description="Laredo yard exit",
        start_latitude=Decimal("27.530600"),
        start_longitude=Decimal("-99.480300"),
        end_latitude=Decimal("28.050000"),
        end_longitude=Decimal("-99.000000"),
        event_count=DEMO_TELEMETRY_EVENT_COUNTS["DEMO-TRUCK-002"],
        speed_mph=Decimal("12"),
        heading=36,
        start_offset_minutes=20,
        rpm=960,
        engine_temp=Decimal("178"),
        fuel_level=Decimal("69"),
        idle_minutes=6,
        reefer_temp=Decimal("37"),
        load_weight=Decimal("19800"),
    ),
    TelemetryTimelineSpec(
        truck_id="DEMO-TRUCK-003",
        fleet_key="refrigerated",
        scenario="stopped",
        location_description="Dallas Mega Cold Storage",
        start_latitude=Decimal("32.807000"),
        start_longitude=Decimal("-96.840000"),
        end_latitude=Decimal("32.807000"),
        end_longitude=Decimal("-96.840000"),
        event_count=DEMO_TELEMETRY_EVENT_COUNTS["DEMO-TRUCK-003"],
        speed_mph=Decimal("0"),
        heading=0,
        start_offset_minutes=40,
        rpm=620,
        engine_temp=Decimal("170"),
        fuel_level=Decimal("54"),
        idle_minutes=0,
        reefer_temp=Decimal("36"),
        load_weight=Decimal("34200"),
    ),
    TelemetryTimelineSpec(
        truck_id="DEMO-TRUCK-004",
        fleet_key="operations",
        scenario="moving",
        location_description="San Antonio outbound",
        start_latitude=Decimal("29.425200"),
        start_longitude=Decimal("-98.494600"),
        end_latitude=Decimal("30.267200"),
        end_longitude=Decimal("-97.743100"),
        event_count=DEMO_TELEMETRY_EVENT_COUNTS["DEMO-TRUCK-004"],
        speed_mph=Decimal("58"),
        heading=39,
        start_offset_minutes=60,
        rpm=1390,
        engine_temp=Decimal("182"),
        fuel_level=Decimal("74"),
        idle_minutes=0,
        reefer_temp=Decimal("37"),
        load_weight=Decimal("27600"),
    ),
    TelemetryTimelineSpec(
        truck_id="DEMO-TRUCK-005",
        fleet_key="operations",
        scenario="maintenance",
        location_description="Amarillo maintenance bay",
        start_latitude=Decimal("35.221900"),
        start_longitude=Decimal("-101.831300"),
        end_latitude=Decimal("35.221900"),
        end_longitude=Decimal("-101.831300"),
        event_count=DEMO_TELEMETRY_EVENT_COUNTS["DEMO-TRUCK-005"],
        speed_mph=Decimal("0"),
        heading=0,
        start_offset_minutes=80,
        rpm=500,
        engine_temp=Decimal("232"),
        fuel_level=Decimal("62"),
        idle_minutes=0,
        reefer_temp=Decimal("37"),
        load_weight=Decimal("16600"),
    ),
    TelemetryTimelineSpec(
        truck_id="DEMO-TRUCK-006",
        fleet_key="operations",
        scenario="idle",
        location_description="El Paso broker-risk staging",
        start_latitude=Decimal("31.761900"),
        start_longitude=Decimal("-106.485000"),
        end_latitude=Decimal("31.820000"),
        end_longitude=Decimal("-106.410000"),
        event_count=DEMO_TELEMETRY_EVENT_COUNTS["DEMO-TRUCK-006"],
        speed_mph=Decimal("3"),
        heading=42,
        start_offset_minutes=100,
        rpm=720,
        engine_temp=Decimal("174"),
        fuel_level=Decimal("66"),
        idle_minutes=8,
        reefer_temp=Decimal("37"),
        load_weight=Decimal("21400"),
    ),
    # DEMO-TRUCK-007 is intentionally unassigned (no load) so it appears as an
    # eligible truck for Phase 2 candidate-load dispatch decisions.
    TelemetryTimelineSpec(
        truck_id="DEMO-TRUCK-007",
        fleet_key="operations",
        scenario="idle",
        location_description="Dallas yard",
        start_latitude=Decimal("32.776700"),
        start_longitude=Decimal("-96.797000"),
        end_latitude=Decimal("32.776700"),
        end_longitude=Decimal("-96.797000"),
        event_count=DEMO_TELEMETRY_EVENT_COUNTS["DEMO-TRUCK-007"],
        speed_mph=Decimal("0"),
        heading=0,
        start_offset_minutes=0,
        rpm=700,
        engine_temp=Decimal("175"),
        fuel_level=Decimal("88"),
        idle_minutes=30,
        reefer_temp=Decimal("37"),
        load_weight=Decimal("0"),
    ),
)


def build_demo_telemetry_events(
    base_date: datetime,
    rng: random.Random,
) -> tuple[TelemetryEventSeed, ...]:
    events: list[TelemetryEventSeed] = []

    for timeline in DEMO_TELEMETRY_TIMELINES:
        events.extend(_build_timeline_events(base_date, rng, timeline))

    return tuple(events)


def _build_timeline_events(
    base_date: datetime,
    rng: random.Random,
    timeline: TelemetryTimelineSpec,
) -> list[TelemetryEventSeed]:
    events = []
    start_time = base_date + timedelta(minutes=timeline.start_offset_minutes)

    for index in range(timeline.event_count):
        progress = _progress(index, timeline.event_count)
        latitude, longitude = _coordinates_for(timeline, progress)

        events.append(
            TelemetryEventSeed(
                truck_id=timeline.truck_id,
                fleet_key=timeline.fleet_key,
                timestamp=start_time + timedelta(
                    minutes=index * TELEMETRY_INTERVAL_MINUTES
                ),
                latitude=latitude,
                longitude=longitude,
                speed=_speed_for(timeline, index),
                heading=timeline.heading,
                reported_status=timeline.scenario,
                location_description=timeline.location_description,
                rpm=_numeric_variation(timeline.rpm, index, 4),
                engine_temp=_decimal_variation(timeline.engine_temp, rng, "1.00"),
                fuel_level=_fuel_level_for(timeline, index),
                idle_minutes=_idle_minutes_for(timeline, index),
                reefer_temp=_decimal_variation(timeline.reefer_temp, rng, "1.00"),
                load_weight=_decimal_variation(timeline.load_weight, rng, "1.00"),
            )
        )

    return events


def _progress(index: int, event_count: int) -> Decimal:
    if event_count <= 1:
        return Decimal("1")
    return Decimal(index) / Decimal(event_count - 1)


def _coordinates_for(
    timeline: TelemetryTimelineSpec,
    progress: Decimal,
) -> tuple[Decimal, Decimal]:
    latitude = timeline.start_latitude + (
        (timeline.end_latitude - timeline.start_latitude) * progress
    )
    longitude = timeline.start_longitude + (
        (timeline.end_longitude - timeline.start_longitude) * progress
    )

    return _quantize(latitude, 6), _quantize(longitude, 6)


def _speed_for(timeline: TelemetryTimelineSpec, index: int) -> Decimal:
    # Each scenario's speed stays inside the band that derives its own label
    # (see derive_operational_status): idle (0, 5], slow (5, 20], moving > 20.
    if timeline.scenario in {"stopped", "maintenance"}:
        return Decimal("0")
    if timeline.scenario == "idle":
        return Decimal("3")
    if timeline.scenario == "slow":
        return Decimal("14") if index > 2 else Decimal("8")
    return timeline.speed_mph


def _fuel_level_for(timeline: TelemetryTimelineSpec, index: int) -> Decimal:
    if timeline.scenario in {"moving", "slow"}:
        return _quantize(timeline.fuel_level - (Decimal(index) * Decimal("0.08")), 2)
    if timeline.scenario == "idle":
        return _quantize(timeline.fuel_level - (Decimal(index) * Decimal("0.03")), 2)
    return timeline.fuel_level


def _idle_minutes_for(timeline: TelemetryTimelineSpec, index: int) -> int:
    if timeline.scenario == "idle":
        return timeline.idle_minutes + (index * TELEMETRY_INTERVAL_MINUTES)
    if timeline.scenario == "stopped":
        return index * TELEMETRY_INTERVAL_MINUTES
    return timeline.idle_minutes


def _numeric_variation(value: int, index: int, step: int) -> int:
    return value + ((index % 5) * step)


def _decimal_variation(
    value: Decimal,
    rng: random.Random,
    quantizer: str,
) -> Decimal:
    adjusted = value + Decimal(str(round(rng.uniform(-0.4, 0.4), 2)))
    return adjusted.quantize(Decimal(quantizer))


def _quantize(value: Decimal, places: int) -> Decimal:
    return value.quantize(Decimal("1." + ("0" * places)))
