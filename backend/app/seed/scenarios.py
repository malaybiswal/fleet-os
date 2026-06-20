from dataclasses import dataclass


@dataclass(frozen=True)
class LoadScenario:
    key: str
    name: str
    description: str
    payout: int
    loaded_miles: int
    deadhead_miles: int
    equipment_type: str
    expected_recommendation: str
    broker_name: str
    origin: str
    destination: str

    def to_mock_load(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "payout": self.payout,
            "loaded_miles": self.loaded_miles,
            "deadhead_miles": self.deadhead_miles,
            "equipment_type": self.equipment_type,
            "expected_recommendation": self.expected_recommendation,
        }


@dataclass(frozen=True)
class DemoScenario:
    key: str
    name: str
    description: str


STRATEGIC_LOAD_SCENARIOS: tuple[LoadScenario, ...] = (
    LoadScenario(
        key="high_pay_bad_load",
        name="High Pay / Bad Load",
        description="Looks attractive because of payout, but weak after deadhead and time risk.",
        payout=4200,
        loaded_miles=1500,
        deadhead_miles=550,
        equipment_type="Dry Van",
        expected_recommendation="AVOID",
        broker_name="Coyote",
        origin="Laredo, TX",
        destination="Denver, CO",
    ),
    LoadScenario(
        key="low_pay_good_load",
        name="Low Pay / Good Load",
        description="Lower gross payout, but short miles and low deadhead make it operationally strong.",
        payout=950,
        loaded_miles=260,
        deadhead_miles=20,
        equipment_type="Dry Van",
        expected_recommendation="RECOMMENDED",
        broker_name="CH Robinson",
        origin="Dallas, TX",
        destination="Houston, TX",
    ),
    LoadScenario(
        key="high_dwell_risk",
        name="High Dwell Risk",
        description="Acceptable mileage economics, but demo scenario represents risky facility dwell.",
        payout=2400,
        loaded_miles=850,
        deadhead_miles=90,
        equipment_type="Reefer",
        expected_recommendation="REVIEW",
        broker_name="Cold Chain Logistics",
        origin="Fort Worth, TX",
        destination="Memphis, TN",
    ),
    LoadScenario(
        key="strong_reload_market",
        name="Strong Reload Market",
        description="Good operational economics and strong destination reload opportunity.",
        payout=3100,
        loaded_miles=1050,
        deadhead_miles=60,
        equipment_type="Dry Van",
        expected_recommendation="RECOMMENDED",
        broker_name="Uber Freight",
        origin="San Antonio, TX",
        destination="Atlanta, GA",
    ),
    LoadScenario(
        key="bad_deadhead",
        name="Bad Deadhead",
        description="Gross RPM looks acceptable, but deadhead destroys profitability.",
        payout=1800,
        loaded_miles=600,
        deadhead_miles=420,
        equipment_type="Flatbed",
        expected_recommendation="AVOID",
        broker_name="TQL",
        origin="Amarillo, TX",
        destination="Oklahoma City, OK",
    ),
)


ADDITIONAL_DEMO_SCENARIOS: tuple[DemoScenario, ...] = (
    DemoScenario(
        key="weak_broker",
        name="Weak Broker",
        description="Broker history creates operational risk despite acceptable lane economics.",
    ),
    DemoScenario(
        key="live_alerting_route",
        name="Live Alerting Route",
        description="Moving truck with live telemetry and unresolved operational alerts.",
    ),
    DemoScenario(
        key="maintenance_truck",
        name="Maintenance Truck",
        description="Truck status is overridden by maintenance regardless of speed.",
    ),
    DemoScenario(
        key="idle_stopped_truck",
        name="Idle / Stopped Truck",
        description="Telemetry covers stopped and idle states for map/status consistency.",
    ),
)


DEMO_SCENARIOS = STRATEGIC_LOAD_SCENARIOS + ADDITIONAL_DEMO_SCENARIOS
