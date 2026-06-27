from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.ingestion.load_ingestion_service import LoadIngestionService
from app.ingestion.normalized_events import NormalizedLoadObject
from app.models.fleet import Fleet
from app.models.load import Load


TEST_DATABASE_URL = "sqlite:///./test_load_ingestion_service.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def test_load_ingestion_upserts_namespaced_fleet_load():
    db = TestingSessionLocal()
    try:
        fleet = Fleet(name="DAT Fleet")
        db.add(fleet)
        db.commit()
        db.refresh(fleet)

        service = LoadIngestionService(db)
        obj = NormalizedLoadObject(
            fleet_id=fleet.id,
            source="dat",
            source_event_id="DAT-001",
            origin="Dallas, TX",
            destination="Houston, TX",
            equipment_type="Dry Van",
            gross_revenue=1250,
            total_miles=245,
            deadhead_miles=20,
            broker_name="DAT Demo Brokerage",
        )

        first = service.ingest(obj)
        second = service.ingest(obj.model_copy(update={"gross_revenue": 1300}))

        loads = db.query(Load).all()
        assert len(loads) == 1
        assert first.id == second.id
        assert second.load_id == f"dat:{fleet.id}:DAT-001"
        assert second.fleet_id == fleet.id
        assert second.source == "dat"
        assert second.external_ref == "DAT-001"
        assert float(second.revenue) == 1300
        assert second.status == "available"
        assert second.last_synced_at is not None
    finally:
        db.close()


def test_load_ingestion_keeps_same_external_ref_isolated_by_fleet():
    db = TestingSessionLocal()
    try:
        fleet_a = Fleet(name="DAT Fleet A")
        fleet_b = Fleet(name="DAT Fleet B")
        db.add_all([fleet_a, fleet_b])
        db.commit()
        db.refresh(fleet_a)
        db.refresh(fleet_b)

        service = LoadIngestionService(db)
        base = {
            "source": "dat",
            "source_event_id": "DAT-SHARED",
            "origin": "Dallas, TX",
            "destination": "Houston, TX",
            "gross_revenue": 1250,
            "total_miles": 245,
        }

        service.ingest(NormalizedLoadObject(fleet_id=fleet_a.id, **base))
        service.ingest(NormalizedLoadObject(fleet_id=fleet_b.id, **base))

        load_ids = {load.load_id for load in db.query(Load).all()}
        assert load_ids == {
            f"dat:{fleet_a.id}:DAT-SHARED",
            f"dat:{fleet_b.id}:DAT-SHARED",
        }
    finally:
        db.close()
