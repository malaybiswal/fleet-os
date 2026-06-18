from app.services.broker_risk import broker_risk_for_load


def test_known_weak_broker_returns_high_risk():
    band, reason = broker_risk_for_load("TQL Risk Desk")

    assert band == "high"
    assert "requires dispatcher review" in reason


def test_reputable_broker_returns_low_risk():
    band, reason = broker_risk_for_load("CH Robinson")

    assert band == "low"
    assert "supports the plan" in reason


def test_unknown_broker_returns_medium_risk():
    band, reason = broker_risk_for_load("Local Spot Desk")

    assert band == "medium"
    assert "neutral" in reason
