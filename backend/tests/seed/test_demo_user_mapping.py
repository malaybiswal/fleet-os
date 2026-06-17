from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base
from app.models.fleet import Fleet
from app.models.user import User
from app.seed.demo_user_mapping import (
    DEMO_USER_EMAILS,
    assign_demo_users,
    assign_user_to_fleet,
)


def _build_test_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine, sessionmaker(bind=engine)


def _create_fleet(db, name: str) -> Fleet:
    fleet = Fleet(name=name)
    db.add(fleet)
    db.commit()
    db.refresh(fleet)
    return fleet


def _create_user(db, email: str, fleet_id: int, uid_suffix: str) -> User:
    user = User(
        email=email,
        firebase_uid=f"test-uid-{uid_suffix}",
        fleet_id=fleet_id,
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_assign_user_to_fleet_remaps_existing_user():
    engine, SessionLocal = _build_test_session_factory()
    try:
        db = SessionLocal()
        wrong_fleet = _create_fleet(db, "Wrong Fleet")
        target_fleet = _create_fleet(db, "Target Fleet")
        user = _create_user(db, "malay.biswal@gmail.com", wrong_fleet.id, "1")

        result = assign_user_to_fleet(db, "malay.biswal@gmail.com", target_fleet.id)
        db.commit()

        db.refresh(user)
        assert result is True
        assert user.fleet_id == target_fleet.id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_assign_user_to_fleet_creates_user_when_missing():
    engine, SessionLocal = _build_test_session_factory()
    try:
        db = SessionLocal()
        target_fleet = _create_fleet(db, "Target Fleet")

        result = assign_user_to_fleet(db, "nobody@example.com", target_fleet.id)
        db.commit()

        assert result is True
        user = db.query(User).filter(User.email == "nobody@example.com").one()
        assert user.fleet_id == target_fleet.id
        assert user.firebase_uid == "demo-seed-nobody@example.com"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_assign_demo_users_maps_all_found_users():
    engine, SessionLocal = _build_test_session_factory()
    try:
        db = SessionLocal()
        wrong_fleet = _create_fleet(db, "Wrong Fleet")
        target_fleet = _create_fleet(db, "Target Fleet")

        for i, email in enumerate(DEMO_USER_EMAILS):
            _create_user(db, email, wrong_fleet.id, str(i))

        mapped = assign_demo_users(db, target_fleet.id)
        db.commit()

        assert set(mapped) == set(DEMO_USER_EMAILS)
        for user in db.query(User).all():
            assert user.fleet_id == target_fleet.id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_assign_demo_users_creates_missing_users():
    engine, SessionLocal = _build_test_session_factory()
    try:
        db = SessionLocal()
        target_fleet = _create_fleet(db, "Target Fleet")

        # No users exist yet — all should be created
        mapped = assign_demo_users(db, target_fleet.id)
        db.commit()

        assert set(mapped) == set(DEMO_USER_EMAILS)
        assert db.query(User).count() == len(DEMO_USER_EMAILS)
        for user in db.query(User).all():
            assert user.fleet_id == target_fleet.id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
