from app.database import SessionLocal
from app.ingestion.telemetry_ingestion_service import TelemetryIngestionService
from app.integrations.simulator.client import fetch_simulated_vehicle_payloads
from app.integrations.simulator.mapper import map_simulator_payload_to_event


def ingest_simulated_telemetry() -> int:
    db = SessionLocal()

    try:
        service = TelemetryIngestionService(db, auto_create_trucks=True)
        payloads = fetch_simulated_vehicle_payloads()

        ingested_count = 0

        for payload in payloads:
            event = map_simulator_payload_to_event(payload)
            service.ingest(event)
            ingested_count += 1

        return ingested_count
    finally:
        db.close()


if __name__ == "__main__":
    count = ingest_simulated_telemetry()
    print(f"Ingested {count} simulated telemetry events")
