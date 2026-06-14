from datetime import datetime, timedelta, timezone

from app.seed.demo_dataset import build_demo_dataset
from app.services import facility_intelligence as fi


BASE_DATE = datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc)

EXPECTED_BANDS = {
    "Houston Crossdock": "good",
    "Atlanta Reload Hub": "good",
    "Denver West DC": "medium",
    "Oklahoma Pipe Yard": "medium",
    "Dallas Mega Cold Storage": "high_risk",
    "Phoenix Grocery DC": "high_risk",
}


def _operational_band(score: float) -> str:
    if score > 75:
        return "good"
    if score >= 40:
        return "medium"
    return "high_risk"


def _score_facility(dataset, facility_name: str) -> float:
    events = [
        event
        for event in dataset.dwell_events
        if event.facility_name == facility_name
    ]
    assert events, f"no demo dwell events for {facility_name}"

    dwell_values = [
        (event.departure_time - event.arrival_time).total_seconds() / 3600.0
        for event in events
    ]
    avg_dwell = sum(dwell_values) / len(dwell_values)

    grace = timedelta(minutes=fi.APPOINTMENT_GRACE_MINUTES)
    appt_on_time = sum(
        1 for event in events if event.loading_start <= event.appointment_time + grace
    )

    detention_visits = sum(1 for hours in dwell_values if hours > fi.DETENTION_FREE_HOURS)
    excess = [max(0.0, hours - fi.DETENTION_FREE_HOURS) for hours in dwell_values]
    avg_excess = sum(excess) / len(excess)

    return fi.operational_score(
        fi.dwell_score(avg_dwell),
        fi.appointment_reliability(len(events), appt_on_time),
        fi.detention_risk(len(dwell_values), detention_visits, avg_excess),
    )


def test_demo_facilities_land_in_expected_score_bands():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)

    for facility_name, expected_band in EXPECTED_BANDS.items():
        score = _score_facility(dataset, facility_name)
        assert _operational_band(score) == expected_band, (
            f"{facility_name}: score {score} not in band {expected_band}"
        )


def test_demo_facility_dataset_is_deterministic_and_linked():
    dataset = build_demo_dataset(seed=32032, base_date=BASE_DATE)

    assert dataset.counts()["facilities"] == 6

    load_ids = {load.load_id for load in dataset.loads}
    facility_names = {facility.name for facility in dataset.facilities}
    for event in dataset.dwell_events:
        assert event.load_id in load_ids
        assert event.facility_name in facility_names
