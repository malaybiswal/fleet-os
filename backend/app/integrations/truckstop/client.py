from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html import escape
from typing import Any, Protocol

import httpx

from app.config import settings
from app.seed.scenarios import STRATEGIC_LOAD_SCENARIOS, LoadScenario


# Bounds and enumerations from the LoadSearch.svc WSDL (LoadSearchCriteria).
RANGE_MIN = 25
RANGE_MAX = 300
PAGE_SIZE_MAX = 200
MAX_EQUIPMENT_CODES = 3

_LOAD_TYPES = {"nothing": "Nothing", "all": "All", "full": "Full", "partial": "Partial"}

_SORT_COLUMNS = {
    value.lower(): value
    for value in (
        "Age",
        "Equipment",
        "LoadType",
        "PickUpDate",
        "OriginCity",
        "OriginState",
        "OriginDistance",
        "DestinationCity",
        "DestinationState",
        "Payment",
        "PaymentAmount",
        "Length",
        "Weight",
        "Days2Pay",
        "Credit",
        "ExperienceFactor",
        "CompanyName",
        "TruckCompanyName",
        "FuelCost",
        "Miles",
        "Mileage",
    )
}


class TruckstopAPIError(RuntimeError):
    pass


class TruckstopAuthenticationError(TruckstopAPIError):
    pass


@dataclass(frozen=True)
class TruckstopCredentials:
    integration_id: str
    username: str
    password: str
    base_url: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    provider_mode: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TruckstopCredentials":
        return cls(
            integration_id=str(payload.get("integration_id") or ""),
            username=str(payload.get("username") or ""),
            password=str(payload.get("password") or ""),
            base_url=payload.get("base_url"),
            filters=payload.get("filters") or {},
            provider_mode=payload.get("provider_mode"),
        )


class TruckstopProvider(Protocol):
    def authenticate(self) -> None:
        ...

    def search_loads(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        ...

    def close(self) -> None:
        ...


class TruckstopClient:
    def __init__(
        self,
        credentials: TruckstopCredentials,
        *,
        base_url: str | None = None,
        timeout_seconds: float = 30,
        http_client: httpx.Client | None = None,
    ):
        self.credentials = credentials
        self.base_url = (
            base_url
            or credentials.base_url
            or settings.TRUCKSTOP_LOADSEARCH_BASE_URL
            or _default_loadsearch_base_url()
        ).rstrip("/")
        self.http_client = http_client or httpx.Client(timeout=timeout_seconds)

    def authenticate(self) -> None:
        if not (
            self.credentials.integration_id
            and self.credentials.username
            and self.credentials.password
        ):
            raise TruckstopAuthenticationError(
                "Truckstop live credentials require integration id, username, and password"
            )

    def search_loads(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        self.authenticate()
        envelope = self._build_search_envelope(
            {**(self.credentials.filters or {}), **(filters or {})}
        )
        response = self.http_client.post(
            self._loadsearch_url(settings.TRUCKSTOP_LOADSEARCH_PATH),
            content=envelope,
            headers={
                "Content-Type": "text/xml",
                "Accept": "text/xml",
                "SOAPAction": settings.TRUCKSTOP_LOADSEARCH_SOAP_ACTION,
            },
        )
        if response.status_code in {401, 403}:
            raise TruckstopAuthenticationError("Truckstop load search authentication failed")
        response.raise_for_status()
        return _extract_search_items(response.text)

    def close(self) -> None:
        self.http_client.close()

    def _loadsearch_url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _build_search_envelope(self, filters: dict[str, Any]) -> str:
        criteria = _criteria_from_filters(filters)
        criteria_xml = "\n".join(
            f"               <web1:{key}>{escape(str(value))}</web1:{key}>"
            for key, value in criteria.items()
            if value not in (None, "")
        )
        # Namespaces verified against the live WSDL (LoadSearch.svc?singleWsdl):
        # web  -> ...WebServices (IntegrationId/Password/UserName),
        # web1 -> ...WebServices.Searching (LoadSearchCriteria),
        # v12  -> webservices.truckstop.com/v12 (operation + searchRequest).
        # Residual unknowns before production: the base EquipmentType code table
        # and the production host (ws.truckstop.com).
        return f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v12="http://webservices.truckstop.com/v12" xmlns:web="http://schemas.datacontract.org/2004/07/WebServices" xmlns:web1="http://schemas.datacontract.org/2004/07/WebServices.Searching">
   <soapenv:Header/>
   <soapenv:Body>
      <v12:GetLoadSearchResults>
         <v12:searchRequest>
            <web:IntegrationId>{escape(self.credentials.integration_id)}</web:IntegrationId>
            <web:Password>{escape(self.credentials.password)}</web:Password>
            <web:UserName>{escape(self.credentials.username)}</web:UserName>
            <web1:Criteria>
{criteria_xml}
            </web1:Criteria>
         </v12:searchRequest>
      </v12:GetLoadSearchResults>
   </soapenv:Body>
</soapenv:Envelope>"""


class MockTruckstopProvider:
    def __init__(self, credentials: TruckstopCredentials):
        self.credentials = credentials
        self.authenticated = False

    def authenticate(self) -> None:
        if not (
            self.credentials.integration_id
            and self.credentials.username
            and self.credentials.password
        ):
            raise TruckstopAuthenticationError(
                "Mock Truckstop credentials require integration id, username, and password"
            )
        self.authenticated = True

    def search_loads(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not self.authenticated:
            self.authenticate()

        tenant = _tenant_token(self.credentials.username)
        effective_filters = {**(self.credentials.filters or {}), **(filters or {})}
        postings = [
            _scenario_to_truckstop_posting(scenario, tenant)
            for scenario in STRATEGIC_LOAD_SCENARIOS
        ]
        return [
            posting
            for posting in postings
            if _matches_filters(posting, effective_filters)
        ]

    def close(self) -> None:
        return None


def build_truckstop_client(
    credentials: TruckstopCredentials,
    *,
    mode: str | None = None,
    http_client: httpx.Client | None = None,
) -> TruckstopProvider:
    selected_mode = (
        mode or credentials.provider_mode or settings.TRUCKSTOP_PROVIDER_MODE
    ).lower()
    if selected_mode == "mock":
        return MockTruckstopProvider(credentials)
    if selected_mode != "live":
        raise ValueError("TRUCKSTOP_PROVIDER_MODE must be 'mock' or 'live'")
    return TruckstopClient(credentials, http_client=http_client)


def _criteria_from_filters(filters: dict[str, Any]) -> dict[str, Any]:
    # Keys are emitted in alphabetical order because the WCF DataContract
    # serializer behind LoadSearch.svc expects Criteria elements in that order.
    return {
        "DestinationCity": _first_present(filters, "DestinationCity", "destination_city"),
        "DestinationCountry": _first_present(
            filters, "DestinationCountry", "destination_country"
        )
        or "USA",
        "DestinationRange": _clamp_int(
            _first_present(filters, "DestinationRange", "destination_range"),
            default=100,
            minimum=RANGE_MIN,
            maximum=RANGE_MAX,
        ),
        "DestinationState": _first_present(
            filters, "DestinationState", "destination_state"
        ),
        "EquipmentType": _normalize_equipment_types(
            _first_present(filters, "EquipmentType", "equipment_type")
        ),
        "HoursOld": _clamp_int(
            _first_present(filters, "HoursOld", "hours_old"),
            default=0,
            minimum=0,
        ),
        "LoadType": _normalize_load_type(
            _first_present(filters, "LoadType", "load_type")
        ),
        "OriginCity": _first_present(filters, "OriginCity", "origin_city"),
        "OriginCountry": _first_present(filters, "OriginCountry", "origin_country")
        or "USA",
        "OriginRange": _clamp_int(
            _first_present(filters, "OriginRange", "origin_range"),
            default=100,
            minimum=RANGE_MIN,
            maximum=RANGE_MAX,
        ),
        "OriginState": _first_present(filters, "OriginState", "origin_state") or "TX",
        "PageNumber": _clamp_int(
            _first_present(filters, "PageNumber", "page_number"),
            default=1,
            minimum=0,
        ),
        "PageSize": _clamp_int(
            _first_present(filters, "PageSize", "page_size"),
            default=100,
            minimum=0,
            maximum=PAGE_SIZE_MAX,
        ),
        "SortBy": _normalize_sort_by(_first_present(filters, "SortBy", "sort_by")),
        "SortDescending": _normalize_sort_descending(
            _first_present(filters, "SortDescending", "sort_descending"),
            default=False,
        ),
    }


def _extract_search_items(xml_text: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise TruckstopAPIError(f"Truckstop load search returned malformed XML: {exc}") from exc

    fault = _first_element(root, "Fault")
    if fault is not None:
        message = _element_text(fault) or "Truckstop SOAP fault"
        if "auth" in message.lower() or "credential" in message.lower():
            raise TruckstopAuthenticationError(message)
        raise TruckstopAPIError(message)

    errors = _first_element(root, "Errors")
    if errors is not None and _element_text(errors):
        message = _element_text(errors) or "Truckstop load search returned errors"
        if "auth" in message.lower() or "credential" in message.lower():
            raise TruckstopAuthenticationError(message)
        raise TruckstopAPIError(message)

    items = [
        _element_to_dict(element)
        for element in root.iter()
        if _local_name(element.tag) == "LoadSearchItem"
    ]
    if not items:
        result = _first_element(root, "SearchResults")
        if result is None:
            raise TruckstopAPIError("Truckstop load search response did not include results")
    return items


def _element_to_dict(element: ET.Element) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for child in list(element):
        name = _local_name(child.tag)
        if child.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true":
            result[name] = None
        elif list(child):
            result[name] = _element_to_dict(child)
        else:
            result[name] = child.text
    return result


def _first_element(root: ET.Element, local_name: str) -> ET.Element | None:
    for element in root.iter():
        if _local_name(element.tag) == local_name:
            return element
    return None


def _element_text(element: ET.Element) -> str:
    return " ".join(text.strip() for text in element.itertext() if text and text.strip())


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _tenant_token(username: str | None) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (username or "anon").lower()).strip("-")
    return slug or "anon"


def _scenario_to_truckstop_posting(
    scenario: LoadScenario,
    tenant: str,
) -> dict[str, Any]:
    origin = _split_place(scenario.origin)
    destination = _split_place(scenario.destination)
    return {
        "ID": f"MOCK-TRUCKSTOP-{tenant}-{scenario.key}",
        "OriginCity": origin.get("city"),
        "OriginState": origin.get("state"),
        "OriginCountry": "USA",
        "OriginDistance": scenario.deadhead_miles,
        "DestinationCity": destination.get("city"),
        "DestinationState": destination.get("state"),
        "DestinationCountry": "USA",
        "DestinationDistance": 0,
        "Equipment": _equipment_code(scenario.equipment_type),
        "EquipmentType": scenario.equipment_type,
        "Payment": f"{scenario.payout:.2f}",
        "Miles": scenario.loaded_miles,
        "LoadType": "Full",
        "CompanyName": scenario.broker_name,
        "PointOfContactPhone": "555-0100",
        "Weight": 42000,
        "Length": 53,
    }


def _matches_filters(posting: dict[str, Any], filters: dict[str, Any]) -> bool:
    equipment = _equipment_code(filters.get("equipment_type") or filters.get("EquipmentType"))
    if equipment and str(posting.get("Equipment", "")).lower() != equipment.lower():
        return False

    origin_state = filters.get("origin_state") or filters.get("OriginState")
    if origin_state and str(posting.get("OriginState", "")).upper() != str(
        origin_state
    ).upper():
        return False

    destination_state = filters.get("destination_state") or filters.get("DestinationState")
    if destination_state and str(posting.get("DestinationState", "")).upper() != str(
        destination_state
    ).upper():
        return False

    return True


def _split_place(place: str) -> dict[str, str]:
    city, _, state = place.partition(",")
    parsed = {"city": city.strip()}
    if state.strip():
        parsed["state"] = state.strip()
    return parsed


def _clamp_int(
    value: Any,
    *,
    default: int,
    minimum: int,
    maximum: int | None = None,
) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    number = max(minimum, number)
    if maximum is not None:
        number = min(maximum, number)
    return number


def _normalize_load_type(value: Any) -> str:
    if value in (None, ""):
        return "Full"
    return _LOAD_TYPES.get(str(value).strip().lower(), "Full")


def _normalize_sort_by(value: Any) -> str:
    if value in (None, ""):
        return "Age"
    return _SORT_COLUMNS.get(str(value).strip().replace(" ", "").lower(), "Age")


def _normalize_sort_descending(value: Any, *, default: bool) -> str:
    if value in (None, ""):
        result = default
    elif isinstance(value, bool):
        result = value
    else:
        result = str(value).strip().lower() in {"true", "1", "yes"}
    return str(result).lower()


def _normalize_equipment_types(value: Any) -> str:
    if value in (None, ""):
        return "V"
    codes = [
        code
        for token in str(value).split(",")
        if token.strip()
        for code in (_equipment_code(token.strip()),)
        if code
    ]
    return ",".join(codes[:MAX_EQUIPMENT_CODES]) or "V"


def _equipment_code(value: Any) -> str | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip().lower()
    return {
        "dry van": "V",
        "van": "V",
        "v": "V",
        "reefer": "R",
        "refrigerated": "R",
        "r": "R",
        "flatbed": "F",
        "flat bed": "F",
        "f": "F",
        "power only": "PO",
        "po": "PO",
    }.get(normalized, str(value))


def _first_present(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return None


def _default_loadsearch_base_url() -> str:
    environment = settings.TRUCKSTOP_ENVIRONMENT.lower()
    if environment == "production":
        return "https://ws.truckstop.com"
    if environment == "staging":
        return "https://testws.truckstop.com"
    raise ValueError("TRUCKSTOP_ENVIRONMENT must be 'staging' or 'production'")
