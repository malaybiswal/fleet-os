from __future__ import annotations

import logging
import re
import time
from datetime import date, datetime
from typing import Any, Mapping

import httpx

from app.config import settings
from app.schemas import CarrierCreate

logger = logging.getLogger(__name__)


SOCRATA_CARRIER_FIELD_MAP: dict[str, str] = {
    "dot_number": "dot_number",
    "legal_name": "legal_name",
    "dba_name": "dba_name",
    "phone": "phone",
    "email_address": "email",
    "phy_street": "address_line1",
    "phy_city": "city",
    "phy_state": "state",
    "phy_zip": "postal_code",
    "phy_country": "country",
    "status_code": "authority_status",
    "add_date": "authority_date",
    "power_units": "power_units",
    "total_drivers": "driver_count",
}
CARRIER_FIELD_TO_SOCRATA_FIELD = {
    carrier_field: socrata_field
    for socrata_field, carrier_field in SOCRATA_CARRIER_FIELD_MAP.items()
}

AUTHORITY_STATUS_MAP = {
    "A": "active",
    "I": "inactive",
    "P": "pending",
}

CARGO_FIELD_MAP: dict[str, str] = {
    "crgo_genfreight": "general_freight",
    "crgo_household": "household_goods",
    "crgo_metalsheetcoil": "metal_sheet_coil",
    "crgo_motoveh": "motor_vehicles",
    "crgo_drivetowaway": "driveaway_towaway",
    "crgo_logs": "logs_poles_beams_lumber",
    "crgo_bldgmat": "building_materials",
    "crgo_mobilehome": "mobile_homes",
    "crgo_machlrg": "machinery_large_objects",
    "crgo_freshprod": "fresh_produce",
    "crgo_liqgas": "liquids_gases",
    "crgo_intermodal": "intermodal_containers",
    "crgo_passengers": "passengers",
    "crgo_oilfield": "oilfield_equipment",
    "crgo_livestock": "livestock",
    "crgo_grainfeedhay": "grain_feed_hay",
    "crgo_coalcoke": "coal_coke",
    "crgo_meat": "meat",
    "crgo_garbage": "garbage_refuse_trash",
    "crgo_usmail": "us_mail",
    "crgo_chem": "chemicals",
    "crgo_drybulk": "dry_bulk",
    "crgo_coldfood": "refrigerated_food",
    "crgo_beverages": "beverages",
    "crgo_paperprod": "paper_products",
    "crgo_utility": "utilities",
    "crgo_farmsupp": "farm_supplies",
    "crgo_construct": "construction",
    "crgo_waterwell": "water_well",
    "crgo_cargoothr": "other",
}


class MalformedCarrierRecord(ValueError):
    """Raised when a Socrata record cannot produce a valid carrier."""


def fetch_socrata_page(
    *,
    limit: int,
    offset: int,
    filters: Mapping[str, str | int] | None = None,
    url: str | None = None,
    client: httpx.Client | None = None,
    max_retries: int = 3,
) -> list[dict[str, Any]]:
    params: dict[str, str | int] = {"$limit": limit, "$offset": offset}
    if filters:
        params.update(filters)

    headers = {"User-Agent": "fleet-os-fmcsa-ingest/1.0"}
    if settings.SOCRATA_APP_TOKEN:
        headers["X-App-Token"] = settings.SOCRATA_APP_TOKEN

    request_url = url or settings.FMCSA_COMPANY_CENSUS_URL
    owns_client = client is None
    http_client = client or httpx.Client(timeout=30)

    try:
        for attempt in range(max_retries + 1):
            try:
                response = http_client.get(request_url, params=params, headers=headers)
                if 500 <= response.status_code < 600 and attempt < max_retries:
                    _sleep_before_retry(attempt)
                    continue

                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, list):
                    raise ValueError("Socrata response must be a JSON list")
                return payload
            except httpx.RequestError:
                if attempt >= max_retries:
                    raise
                _sleep_before_retry(attempt)

        return []
    finally:
        if owns_client:
            http_client.close()


def transform_company_census_record(record: Mapping[str, Any]) -> CarrierCreate:
    dot_number = _clean_str(_mapped_value(record, "dot_number"))
    legal_name = _clean_str(_mapped_value(record, "legal_name"))

    if dot_number is None:
        raise MalformedCarrierRecord("missing dot_number")
    if legal_name is None:
        raise MalformedCarrierRecord("missing legal_name")

    return CarrierCreate(
        dot_number=dot_number,
        mc_number=_mc_number(record),
        legal_name=legal_name,
        dba_name=_clean_str(_mapped_value(record, "dba_name")),
        phone=_format_phone(_mapped_value(record, "phone")),
        email=_clean_str(_mapped_value(record, "email")),
        address_line1=_clean_str(_mapped_value(record, "address_line1")),
        city=_clean_str(_mapped_value(record, "city")),
        state=_clean_str(_mapped_value(record, "state")),
        postal_code=_clean_str(_mapped_value(record, "postal_code")),
        country=_clean_str(_mapped_value(record, "country")),
        authority_status=_authority_status(
            _mapped_value(record, "authority_status"),
            dot_number,
        ),
        authority_date=_parse_date(_mapped_value(record, "authority_date")),
        power_units=_parse_int(_mapped_value(record, "power_units")),
        driver_count=_parse_int(_mapped_value(record, "driver_count")),
        cargo_types=_cargo_types(record),
    )


def _sleep_before_retry(attempt: int) -> None:
    time.sleep(0.25 * (2**attempt))


def _format_phone(raw: Any) -> str | None:
    cleaned = _clean_str(raw)
    if not cleaned:
        return None
    digits = re.sub(r"\D", "", cleaned)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    if len(digits) == 11 and digits[0] == "1":
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return cleaned


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _mapped_value(record: Mapping[str, Any], carrier_field: str) -> Any:
    return record.get(CARRIER_FIELD_TO_SOCRATA_FIELD[carrier_field])


def _mc_number(record: Mapping[str, Any]) -> str | None:
    prefix = _clean_str(record.get("docket1prefix"))
    number = _clean_str(record.get("docket1"))
    if not prefix or not number:
        return None
    return f"{prefix}{number}"


def _authority_status(value: Any, dot_number: str) -> str | None:
    status_code = _clean_str(value)
    if status_code is None:
        return None

    upper_status = status_code.upper()
    mapped_status = AUTHORITY_STATUS_MAP.get(upper_status)
    if mapped_status is not None:
        return mapped_status

    logger.warning(
        "Unexpected FMCSA authority status code for dot_number=%s: %s",
        dot_number,
        status_code,
    )
    return status_code.lower()


def _parse_date(value: Any) -> date | None:
    text = _clean_str(value)
    if text is None:
        return None

    date_part = text.split()[0]
    try:
        return datetime.strptime(date_part, "%Y%m%d").date()
    except ValueError:
        logger.warning("Invalid FMCSA date value: %s", text)
        return None


def _parse_int(value: Any) -> int | None:
    text = _clean_str(value)
    if text is None:
        return None

    try:
        return int(text.replace(",", ""))
    except ValueError:
        logger.warning("Invalid FMCSA integer value: %s", text)
        return None


def _cargo_types(record: Mapping[str, Any]) -> list[str] | None:
    cargo_types = [
        cargo_type
        for field_name, cargo_type in CARGO_FIELD_MAP.items()
        if _clean_str(record.get(field_name)) is not None
    ]
    return cargo_types or None
