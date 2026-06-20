from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base
from app.models.fleet import Fleet
from app.models.user import User
from app.seed import demo_environment
from app.seed.demo_user_mapping import DEMO_USER_EMAILS
from app.seed.mock_fleets import DEMO_FLEET_NAMES
from app.seed.persist import count_demo_data
from app.simulator.telemetry import DEMO_TELEMETRY_EVENT_TOTAL


def test_demo_environment_cli_dry_run_does_not_write(capsys):
    engine, SessionLocal = _build_test_session_factory()
    try:
        exit_code = demo_environment.main(["--dry-run"], session_factory=SessionLocal)

        db = SessionLocal()
        try:
            assert exit_code == 0
            assert db.query(Fleet).filter(Fleet.name.in_(DEMO_FLEET_NAMES)).count() == 0
        finally:
            db.close()

        output = capsys.readouterr().out
        assert "Demo seed dry run complete" in output
        assert "Would create:" in output
    finally:
        Base.metadata.drop_all(bind=engine)


def test_demo_environment_cli_creates_demo_data(capsys):
    engine, SessionLocal = _build_test_session_factory()
    try:
        exit_code = demo_environment.main([], session_factory=SessionLocal)

        db = SessionLocal()
        try:
            counts = count_demo_data(db)
            assert exit_code == 0
            assert counts["fleets"] == 2
            assert counts["loads"] == 24  # 6 strategic + 15 facility history + 3 candidate loads
            assert counts["facilities"] == 6
            assert counts["telemetry_events"] == DEMO_TELEMETRY_EVENT_TOTAL
        finally:
            db.close()

        output = capsys.readouterr().out
        assert "Demo seed complete" in output
        assert "Created:" in output
    finally:
        Base.metadata.drop_all(bind=engine)


def _build_test_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine, sessionmaker(bind=engine)


def test_demo_environment_cli_maps_demo_users_to_operations_fleet(capsys):
    engine, SessionLocal = _build_test_session_factory()
    try:
        # Pre-create demo users on a wrong fleet so they exist to be remapped
        db = SessionLocal()
        wrong_fleet = Fleet(name="Wrong Fleet")
        db.add(wrong_fleet)
        db.commit()
        db.refresh(wrong_fleet)
        for i, email in enumerate(DEMO_USER_EMAILS):
            db.add(User(
                email=email,
                firebase_uid=f"test-uid-{i}",
                fleet_id=wrong_fleet.id,
                role="admin",
            ))
        db.commit()
        db.close()

        exit_code = demo_environment.main([], session_factory=SessionLocal)

        db = SessionLocal()
        try:
            assert exit_code == 0
            ops_fleet = (
                db.query(Fleet).filter(Fleet.name == DEMO_FLEET_NAMES[0]).one()
            )
            for email in DEMO_USER_EMAILS:
                user = db.query(User).filter(User.email == email).one()
                assert user.fleet_id == ops_fleet.id, (
                    f"{email} not mapped to operations fleet"
                )
        finally:
            db.close()

        output = capsys.readouterr().out
        assert "Mapped Users:" in output
        assert "malay.biswal@gmail.com" in output
    finally:
        Base.metadata.drop_all(bind=engine)


def test_demo_environment_cli_dry_run_skips_user_mapping(capsys):
    engine, SessionLocal = _build_test_session_factory()
    try:
        db = SessionLocal()
        wrong_fleet = Fleet(name="Wrong Fleet")
        db.add(wrong_fleet)
        db.commit()
        db.refresh(wrong_fleet)
        wrong_fleet_id = wrong_fleet.id  # capture before session closes
        db.add(User(
            email="malay.biswal@gmail.com",
            firebase_uid="test-uid-dry",
            fleet_id=wrong_fleet_id,
            role="admin",
        ))
        db.commit()
        db.close()

        exit_code = demo_environment.main(["--dry-run"], session_factory=SessionLocal)

        db = SessionLocal()
        try:
            assert exit_code == 0
            user = db.query(User).filter(
                User.email == "malay.biswal@gmail.com"
            ).one()
            assert user.fleet_id == wrong_fleet_id
        finally:
            db.close()

        output = capsys.readouterr().out
        assert "Demo seed dry run complete" in output
        assert "Mapped Users:" not in output
    finally:
        Base.metadata.drop_all(bind=engine)
