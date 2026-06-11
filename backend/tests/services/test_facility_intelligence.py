from app.services import facility_intelligence as fi


class TestDwellScore:
    def test_matches_existing_scorecard_convention(self):
        assert fi.dwell_score(0) == 100
        assert fi.dwell_score(2.5) == 75
        assert fi.dwell_score(10) == 0

    def test_clamps_at_zero(self):
        assert fi.dwell_score(15) == 0


class TestAppointmentReliability:
    def test_no_appointment_data_returns_none(self):
        assert fi.appointment_reliability(0, 0) is None

    def test_percentage(self):
        assert fi.appointment_reliability(4, 3) == 75.0
        assert fi.appointment_reliability(5, 5) == 100.0
        assert fi.appointment_reliability(5, 0) == 0.0


class TestDetentionRisk:
    def test_no_visits_returns_none(self):
        assert fi.detention_risk(0, 0, 0.0) is None

    def test_no_detention_is_zero(self):
        assert fi.detention_risk(5, 0, 0.0) == 0

    def test_every_visit_max_excess_is_max(self):
        assert fi.detention_risk(4, 4, 4.0) == 100

    def test_magnitude_caps_at_one(self):
        assert fi.detention_risk(4, 4, 12.0) == 100

    def test_mixed(self):
        # frequency 0.5 -> 30, magnitude 2/4 -> 20
        assert fi.detention_risk(4, 2, 2.0) == 50


class TestDetentionRiskBand:
    def test_none_passthrough(self):
        assert fi.detention_risk_band(None) is None

    def test_band_boundaries(self):
        assert fi.detention_risk_band(34) == "low"
        assert fi.detention_risk_band(35) == "medium"
        assert fi.detention_risk_band(65) == "medium"
        assert fi.detention_risk_band(66) == "high"


class TestOperationalScore:
    def test_all_components(self):
        # 0.4*80 + 0.3*90 + 0.3*(100-20) = 32 + 27 + 24 = 83
        assert fi.operational_score(80, 90, 20) == 83

    def test_renormalizes_when_reliability_missing(self):
        # (0.4*80 + 0.3*80) / 0.7 = 80
        assert fi.operational_score(80, None, 20) == 80

    def test_all_missing_returns_none(self):
        assert fi.operational_score(None, None, None) is None

    def test_clamped_to_range(self):
        assert fi.operational_score(100, 100, 0) == 100
        assert fi.operational_score(0, 0, 100) == 0


class TestConfidence:
    def test_thresholds(self):
        assert fi.confidence(0) == "low"
        assert fi.confidence(2) == "low"
        assert fi.confidence(3) == "medium"
        assert fi.confidence(9) == "medium"
        assert fi.confidence(10) == "high"
