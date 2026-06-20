from typing import Literal

BrokerRiskBand = Literal["low", "medium", "high"]


BROKER_RISK_BY_NAME: dict[str, BrokerRiskBand] = {
    "ch robinson": "low",
    "c.h. robinson": "low",
    "convoy": "low",
    "j.b. hunt": "low",
    "tql": "medium",
    "tql risk desk": "high",
}


def broker_risk_for_load(broker_name: str | None) -> tuple[BrokerRiskBand, str]:
    if not broker_name or not broker_name.strip():
        return "medium", "Broker risk is neutral because no broker name is available"

    normalized = broker_name.strip().lower()
    risk_band = BROKER_RISK_BY_NAME.get(normalized, "medium")

    if risk_band == "high":
        return "high", f"High broker risk from {broker_name} requires dispatcher review"
    if risk_band == "low":
        return "low", f"Low broker risk from {broker_name} supports the plan"
    return "medium", f"Broker risk from {broker_name} is neutral"
