import pytest

from app.models import (
    Alert,
    Carrier,
    CarrierSnapshot,
    Driver,
    DwellEvent,
    Load,
    OutreachNote,
    Tag,
    TelemetryEvent,
    Truck,
)
from app.schemas import (
    AlertResponse,
    CarrierListItem,
    CarrierRead,
    CarrierSnapshotRead,
    DriverResponse,
    DwellEventResponse,
    LoadResponse,
    OutreachNoteRead,
    TagRead,
    TelemetryEventResponse,
    TruckResponse,
)


SCHEMA_FIELD_EXCEPTIONS = {
    (OutreachNote, OutreachNoteRead): {"note": "content"},
}


@pytest.mark.parametrize(
    ("model", "schema"),
    [
        (Carrier, CarrierRead),
        (Carrier, CarrierListItem),
        (CarrierSnapshot, CarrierSnapshotRead),
        (OutreachNote, OutreachNoteRead),
        (Tag, TagRead),
        (Alert, AlertResponse),
        (Driver, DriverResponse),
        (DwellEvent, DwellEventResponse),
        (Load, LoadResponse),
        (TelemetryEvent, TelemetryEventResponse),
        (Truck, TruckResponse),
    ],
)
def test_response_schema_exposes_all_model_columns(model, schema):
    model_columns = set(model.__table__.columns.keys())
    schema_fields = set(schema.model_fields.keys())
    exceptions = SCHEMA_FIELD_EXCEPTIONS.get((model, schema), {})

    missing = model_columns - schema_fields - set(exceptions)

    assert missing == set()
    for schema_field in exceptions.values():
        assert schema_field in schema_fields
