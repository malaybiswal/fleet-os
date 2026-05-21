import argparse
import csv
import io
import json
import ssl
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.carrier import Carrier


VIEW_ID = "az4n-8mr2"
BASE_URL = f"https://data.transportation.gov/api/views/{VIEW_ID}"
RESOURCE_URL = f"https://data.transportation.gov/resource/{VIEW_ID}.csv"
REGIONAL_STATES = ("TX", "OK", "LA", "AR", "NM")
DEFAULT_PAGE_SIZE = 50_000
CARGO_SEPARATOR = "|"

CARGO_FIELDS = {
    "crgo_genfreight": "General Freight",
    "crgo_household": "Household Goods",
    "crgo_metalsheet": "Metal Sheets",
    "crgo_motoveh": "Motor Vehicles",
    "crgo_drivetow": "Driveaway/Towaway"    ,
    "crgo_logpole": "Logs/Poles",
    "crgo_bldgmat": "Building Materials",
    "crgo_mobilehome": "Mobile Homes",
    "crgo_machlrg": "Machinery",
    "crgo_produce": "Fresh Produce",
    "crgo_liqgas": "Liquids/Gases",
    "crgo_intermodal": "Intermodal Containers",
    "crgo_passengers": "Passengers",
    "crgo_oilfield": "Oilfield Equipment",
    "crgo_livestock": "Livestock",
    "crgo_grainfeed": "Grain/Feed/Hay",
    "crgo_coalcoke": "Coal/Coke",
    "crgo_meat": "Meat",
    "crgo_garbage": "Garbage/Refuse",
    "crgo_usmail": "US Mail",
    "crgo_chem": "Chemicals",
    "crgo_drybulk": "Dry Bulk",
    "crgo_coldfood": "Refrigerated Food",
    "crgo_beverages": "Beverages",
    "crgo_paperprod": "Paper Products",
    "crgo_utility": "Utilities",
    "crgo_farmsupp": "Farm Supplies",
    "crgo_construct": "Construction",
    "crgo_waterwell": "Water Well",
    "crgo_cargoothr": "Other",
}


def ssl_context() -> ssl.SSLContext:
    default_paths = ssl.get_default_verify_paths()
    if default_paths.cafile:
        return ssl.create_default_context()

    for cafile in ("/etc/ssl/cert.pem", "/opt/homebrew/etc/ca-certificates/cert.pem"):
        if Path(cafile).exists():
            return ssl.create_default_context(cafile=cafile)

    return ssl.create_default_context()


def open_url(url: str):
    request = Request(url, headers={"User-Agent": "fleet-os-fmcsa-import/1.0"})
    return urlopen(request, context=ssl_context())


def fetch_metadata() -> dict:
    with open_url(BASE_URL) as response:
        return json.loads(response.read().decode("utf-8"))


def source_rows_updated_at(metadata: dict) -> datetime | None:
    value = metadata.get("rowsUpdatedAt")
    if value is None:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)


def regional_where() -> str:
    states = ",".join(f"'{state}'" for state in REGIONAL_STATES)
    return f"phy_state in({states})"


def csv_url(limit: int, offset: int, where: str | None, order: str | None = None) -> str:
    params: dict[str, str | int] = {"$limit": limit, "$offset": offset}
    if where:
        params["$where"] = where
    if order:
        params["$order"] = order
    return f"{RESOURCE_URL}?{urlencode(params)}"


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def clean_int(value: str | None) -> int | None:
    cleaned = clean_text(value)
    if cleaned is None:
        return None
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def normalize_cargo_types(row: dict[str, str]) -> list[str]:
    cargo_types = [
        label
        for field_name, label in CARGO_FIELDS.items()
        if clean_text(row.get(field_name))
    ]

    other_description = clean_text(row.get("crgo_cargoothr_desc"))
    if other_description and "Other" in cargo_types:
        cargo_types[cargo_types.index("Other")] = f"Other: {other_description}"

    return cargo_types


def serialize_cargo_types(cargo_types: Iterable[str]) -> str | None:
    values = [cargo_type for cargo_type in cargo_types if cargo_type]
    if not values:
        return None
    return CARGO_SEPARATOR.join(values)


def first_present(*values: str | None) -> str | None:
    for value in values:
        cleaned = clean_text(value)
        if cleaned is not None:
            return cleaned
    return None


def carrier_record_from_row(
    row: dict[str, str],
    imported_at: datetime,
    rows_updated_at: datetime | None,
) -> dict | None:
    dot_number = clean_int(row.get("dot_number"))
    if dot_number is None:
        return None

    return {
        "dot_number": dot_number,
        "legal_name": clean_text(row.get("legal_name")),
        "dba_name": clean_text(row.get("dba_name")),
        "docket1_prefix": clean_text(row.get("docket1prefix")),
        "docket1_number": clean_text(row.get("docket1")),
        "docket1_status_code": clean_text(row.get("docket1_status_code")),
        "docket2_prefix": clean_text(row.get("docket2prefix")),
        "docket2_number": clean_text(row.get("docket2")),
        "docket2_status_code": clean_text(row.get("docket2_status_code")),
        "docket3_prefix": clean_text(row.get("docket3prefix")),
        "docket3_number": clean_text(row.get("docket3")),
        "docket3_status_code": clean_text(row.get("docket3_status_code")),
        "authority_status": first_present(
            row.get("docket1_status_code"),
            row.get("docket2_status_code"),
            row.get("docket3_status_code"),
        ),
        "phone": clean_text(row.get("phone")),
        "email_address": clean_text(row.get("email_address")),
        "phy_street": clean_text(row.get("phy_street")),
        "phy_city": clean_text(row.get("phy_city")),
        "phy_state": clean_text(row.get("phy_state")),
        "phy_zip": clean_text(row.get("phy_zip")),
        "phy_country": clean_text(row.get("phy_country")),
        "carrier_mailing_street": clean_text(row.get("carrier_mailing_street")),
        "carrier_mailing_city": clean_text(row.get("carrier_mailing_city")),
        "carrier_mailing_state": clean_text(row.get("carrier_mailing_state")),
        "carrier_mailing_zip": clean_text(row.get("carrier_mailing_zip")),
        "carrier_mailing_country": clean_text(row.get("carrier_mailing_country")),
        "status_code": clean_text(row.get("status_code")),
        "carrier_operation": clean_text(row.get("carrier_operation")),
        "classdef": clean_text(row.get("classdef")),
        "hm_ind": clean_text(row.get("hm_ind")),
        "business_org_desc": clean_text(row.get("business_org_desc")),
        "power_units": clean_int(row.get("power_units")),
        "truck_units": clean_int(row.get("truck_units")),
        "bus_units": clean_int(row.get("bus_units")),
        "total_drivers": clean_int(row.get("total_drivers")),
        "total_cdl": clean_int(row.get("total_cdl")),
        "mcs150_date": clean_text(row.get("mcs150_date")),
        "add_date": clean_text(row.get("add_date")),
        "safety_rating": clean_text(row.get("safety_rating")),
        "safety_rating_date": clean_text(row.get("safety_rating_date")),
        "review_type": clean_text(row.get("review_type")),
        "review_date": clean_text(row.get("review_date")),
        "cargo_types": serialize_cargo_types(normalize_cargo_types(row)),
        "source_rows_updated_at": rows_updated_at,
        "imported_at": imported_at,
    }


def upsert_carriers(db: Session, records: list[dict]) -> int:
    if not records:
        return 0

    table = Carrier.__table__
    statement = insert(table).values(records)
    update_columns = {
        column.name: getattr(statement.excluded, column.name)
        for column in table.columns
        if column.name not in {"id", "dot_number"}
    }
    db.execute(
        statement.on_conflict_do_update(
            index_elements=["dot_number"],
            set_=update_columns,
        )
    )
    db.commit()
    return len(records)


def import_company_census(
    db: Session,
    scope: str,
    limit: int | None,
    page_size: int,
) -> int:
    metadata = fetch_metadata()
    rows_updated_at = source_rows_updated_at(metadata)
    where = regional_where() if scope == "regional" else None
    order = "phy_state DESC, dot_number" if scope == "regional" else None
    imported_at = datetime.now(timezone.utc)
    total_imported = 0
    offset = 0

    while True:
        remaining = None if limit is None else limit - total_imported
        if remaining is not None and remaining <= 0:
            break

        request_limit = page_size if remaining is None else min(page_size, remaining)
        with open_url(csv_url(request_limit, offset, where, order)) as response:
            text_response = io.TextIOWrapper(response, encoding="utf-8", newline="")
            reader = csv.DictReader(text_response)
            page_rows = 0
            records = []
            for row in reader:
                page_rows += 1
                record = carrier_record_from_row(
                    row,
                    imported_at=imported_at,
                    rows_updated_at=rows_updated_at,
                )
                if record:
                    records.append(record)

        upsert_carriers(db, records)
        total_imported += len(records)
        print(f"Imported {total_imported:,} carriers")

        if page_rows < request_limit:
            break
        offset += request_limit

    return total_imported


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import FMCSA Company Census carriers")
    parser.add_argument("--scope", choices=("regional", "full"), default="regional")
    parser.add_argument("--limit", type=int, help="Optional maximum rows to import")
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be greater than zero")
    if args.page_size < 1:
        raise SystemExit("--page-size must be greater than zero")

    db = SessionLocal()
    try:
        total_imported = import_company_census(
            db,
            scope=args.scope,
            limit=args.limit,
            page_size=args.page_size,
        )
    finally:
        db.close()

    print(f"Done. Imported {total_imported:,} carriers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
