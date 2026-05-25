from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any, Mapping


PRIMARY_STATES = {"TX", "CA", "FL", "GA", "IL", "OH", "PA", "NC", "TN", "AZ"}
SECONDARY_STATES = {"IN", "MO", "WI", "MI", "NJ", "VA", "SC", "KY", "OK", "AR"}

HIGH_VALUE_CARGO = {"refrigerated_food", "fresh_produce", "meat", "beverages"}
MEDIUM_VALUE_CARGO = {
    "general_freight",
    "building_materials",
    "paper_products",
    "retail_goods",
}

CARGO_SYNONYMS = {
    "reefer": "refrigerated_food",
    "refrigerated": "refrigerated_food",
    "refrigerated_food": "refrigerated_food",
    "cold_food": "refrigerated_food",
    "coldfood": "refrigerated_food",
    "fresh_produce": "fresh_produce",
    "produce": "fresh_produce",
    "freshprod": "fresh_produce",
    "meat": "meat",
    "beverage": "beverages",
    "beverages": "beverages",
    "general_freight": "general_freight",
    "genfreight": "general_freight",
    "building_materials": "building_materials",
    "bldgmat": "building_materials",
    "paper_products": "paper_products",
    "paperprod": "paper_products",
    "retail": "retail_goods",
    "retail_goods": "retail_goods",
    "household": "household_goods",
    "household_goods": "household_goods",
    "farm_supplies": "farm_supplies",
    "farmsupp": "farm_supplies",
    "garbage": "garbage_refuse_trash",
    "refuse": "garbage_refuse_trash",
    "garbage_refuse": "garbage_refuse_trash",
    "garbage_refuse_trash": "garbage_refuse_trash",
    "logging": "logs_poles_beams_lumber",
    "logs": "logs_poles_beams_lumber",
    "logpole": "logs_poles_beams_lumber",
    "logs_poles_beams_lumber": "logs_poles_beams_lumber",
}


def calculate_carrier_lead_score(
    carrier: Mapping[str, Any] | object,
    *,
    today: date | None = None,
) -> int:
    score = 0
    score += _state_bonus(_value(carrier, "state"))
    score += _cargo_bonus(_value(carrier, "cargo_types"))
    score += _fleet_size_bonus(_value(carrier, "power_units"))
    score += _contactability_bonus(
        phone=_value(carrier, "phone"),
        email=_value(carrier, "email"),
    )
    score += _active_authority_bonus(_value(carrier, "authority_status"))
    score += _recent_authority_bonus(_value(carrier, "authority_date"), today=today)
    return max(0, min(100, score))


def normalize_cargo_token(value: Any) -> str | None:
    if value is None:
        return None

    token = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
    token = re.sub(r"_+", "_", token)
    if not token:
        return None
    return CARGO_SYNONYMS.get(token, token)


def _value(carrier: Mapping[str, Any] | object, field_name: str) -> Any:
    if isinstance(carrier, Mapping):
        return carrier.get(field_name)
    return getattr(carrier, field_name, None)


def _state_bonus(raw_state: Any) -> int:
    state = _clean_str(raw_state)
    if state is None:
        return 0

    upper_state = state.upper()
    if upper_state in PRIMARY_STATES:
        return 15
    if upper_state in SECONDARY_STATES:
        return 8
    return 0


def _cargo_bonus(raw_cargo_types: Any) -> int:
    normalized = {
        token
        for cargo_type in _cargo_values(raw_cargo_types)
        if (token := normalize_cargo_token(cargo_type)) is not None
    }
    if normalized & HIGH_VALUE_CARGO:
        return 20
    if normalized & MEDIUM_VALUE_CARGO:
        return 10
    return 0


def _cargo_values(raw_cargo_types: Any) -> list[Any]:
    if raw_cargo_types is None:
        return []
    if isinstance(raw_cargo_types, str):
        return [
            value.strip()
            for value in re.split(r"[|,]", raw_cargo_types)
            if value.strip()
        ]
    if isinstance(raw_cargo_types, (list, tuple, set)):
        return list(raw_cargo_types)
    return [raw_cargo_types]


def _fleet_size_bonus(raw_power_units: Any) -> int:
    power_units = _int_value(raw_power_units)
    if power_units is None:
        return 0
    if 1 <= power_units <= 4:
        return 8
    if 5 <= power_units <= 25:
        return 20
    if 26 <= power_units <= 50:
        return 12
    if 51 <= power_units <= 100:
        return 3
    return 0


def _contactability_bonus(*, phone: Any, email: Any) -> int:
    has_phone = _clean_str(phone) is not None
    has_email = _clean_str(email) is not None

    if has_phone and has_email:
        return 20
    if has_phone:
        return 8
    if has_email:
        return 12
    return 0


def _active_authority_bonus(raw_authority_status: Any) -> int:
    status = _clean_str(raw_authority_status)
    if not status:
        return 0
    lower_status = status.lower()
    if lower_status == "active":
        return 10
    if lower_status == "pending":
        return 3
    return 0


def _recent_authority_bonus(raw_authority_date: Any, *, today: date | None) -> int:
    authority_date = _date_value(raw_authority_date)
    if authority_date is None:
        return 0
    effective_today = today or date.today()
    age_days = (effective_today - authority_date).days
    if age_days < 0:
        age_days = 0
    if age_days <= 365:
        return 15
    if age_days <= 3 * 365:
        return 10
    if age_days <= 5 * 365:
        return 5
    return 0


def _date_value(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _clean_str(value)
    if text is None:
        return None
    date_part = text.split("T")[0].split()[0]
    for date_format in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(date_part, date_format).date()
        except ValueError:
            continue
    return None


def _int_value(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value).replace(",", "").strip())
    except ValueError:
        return None


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None
