from app.seed.mock_loads import STRATEGIC_MOCK_LOADS, get_evaluated_mock_loads


def test_strategic_mock_loads_exist():
    assert len(STRATEGIC_MOCK_LOADS) == 5

    names = {load["name"] for load in STRATEGIC_MOCK_LOADS}

    assert "High Pay / Bad Load" in names
    assert "Low Pay / Good Load" in names
    assert "High Dwell Risk" in names
    assert "Strong Reload Market" in names
    assert "Bad Deadhead" in names


def test_mock_loads_can_be_evaluated():
    evaluated_loads = get_evaluated_mock_loads()

    assert len(evaluated_loads) == 5

    for load in evaluated_loads:
        assert load["actual_recommendation"] in {"TAKE", "REVIEW", "AVOID"}
        assert load["metrics"]["gross_rpm"] > 0
        assert load["metrics"]["deadhead_adjusted_rpm"] > 0
        assert 0 <= load["metrics"]["operational_score"] <= 100


def test_mock_loads_cover_recommendation_outcomes():
    evaluated_loads = get_evaluated_mock_loads()
    recommendations = {load["actual_recommendation"] for load in evaluated_loads}

    assert "TAKE" in recommendations
    assert "AVOID" in recommendations
    assert "REVIEW" in recommendations


def test_mock_loads_carry_destination_facility_risk():
    evaluated_loads = get_evaluated_mock_loads()
    by_name = {load["name"]: load for load in evaluated_loads}

    high_dwell = by_name["High Dwell Risk"]["destination_facility"]
    assert high_dwell is not None
    assert high_dwell["facility_name"] == "Dallas Mega Cold Storage"
    assert high_dwell["detention_risk_band"] == "high"

    good_load = by_name["Low Pay / Good Load"]["destination_facility"]
    assert good_load is not None
    assert good_load["facility_name"] == "Houston Crossdock"
    assert good_load["detention_risk_band"] == "low"
