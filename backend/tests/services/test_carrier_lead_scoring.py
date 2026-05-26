from datetime import date, timedelta

from app.services.carrier_lead_scoring import calculate_carrier_lead_score


TODAY = date(2026, 5, 25)


def test_high_fit_carrier_score_clamps_to_100():
    score = calculate_carrier_lead_score(
        {
            "state": "TX",
            "cargo_types": ["refrigerated_food"],
            "power_units": 12,
            "phone": "555-123-4567",
            "email": "ops@example.com",
            "authority_status": "active",
            "authority_date": TODAY - timedelta(days=30),
        },
        today=TODAY,
    )

    assert score == 100


def test_low_fit_carrier_score_clamps_to_zero():
    score = calculate_carrier_lead_score(
        {
            "state": "WY",
            "cargo_types": ["household_goods"],
            "power_units": 150,
            "phone": None,
            "email": None,
            "authority_status": "inactive",
            "authority_date": TODAY - timedelta(days=365 * 10),
        },
        today=TODAY,
    )

    assert score == 0


def test_contactability_combined_cases_are_not_double_counted():
    base = {"authority_date": TODAY - timedelta(days=365 * 10)}

    assert calculate_carrier_lead_score({**base, "phone": "555", "email": "a@b.com"}, today=TODAY) == 20
    assert calculate_carrier_lead_score({**base, "phone": "555", "email": None}, today=TODAY) == 8
    assert calculate_carrier_lead_score({**base, "phone": None, "email": "a@b.com"}, today=TODAY) == 12
    assert calculate_carrier_lead_score({**base, "phone": None, "email": None}, today=TODAY) == 0


def test_cargo_synonyms_use_highest_single_bonus():
    base = {"phone": "555", "authority_date": TODAY - timedelta(days=365 * 10)}

    high_score = calculate_carrier_lead_score(
        {**base, "cargo_types": ["Fresh Produce", "general freight"]},
        today=TODAY,
    )
    medium_score = calculate_carrier_lead_score(
        {**base, "cargo_types": ["building materials"]},
        today=TODAY,
    )

    assert high_score == 28
    assert medium_score == 18


def test_missing_fields_still_produce_deterministic_score():
    assert calculate_carrier_lead_score({}, today=TODAY) == 0


def test_authority_status_and_recency_tiers():
    assert calculate_carrier_lead_score(
        {
            "authority_status": "pending",
            "authority_date": TODAY - timedelta(days=400),
        },
        today=TODAY,
    ) == 13
    assert calculate_carrier_lead_score(
        {"authority_status": "inactive", "authority_date": TODAY - timedelta(days=4 * 365)},
        today=TODAY,
    ) == 5
