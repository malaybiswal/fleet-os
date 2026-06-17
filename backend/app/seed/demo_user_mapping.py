import logging

from sqlalchemy.orm import Session

from app.models.user import User

logger = logging.getLogger(__name__)

DEMO_USER_EMAILS: tuple[str, ...] = (
    "perfnews@gmail.com",
    "malay.biswal@gmail.com",
    "dev@fleetos.local",
    "pribiswal7@gmail.com",
)


def assign_user_to_fleet(db: Session, email: str, fleet_id: int) -> bool:
    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None:
        # When AUTH_DISABLED=True, users are never created via Firebase login,
        # so we create them here with a synthetic UID so the seed is self-contained.
        user = User(
            email=email,
            firebase_uid=f"demo-seed-{email}",
            fleet_id=fleet_id,
            role="admin",
        )
        db.add(user)
        logger.info("Created demo user %s -> fleet %s", email, fleet_id)
        return True
    user.fleet_id = fleet_id
    logger.info("Mapped %s -> fleet %s", email, fleet_id)
    return True


def assign_demo_users(db: Session, fleet_id: int) -> list[str]:
    for email in DEMO_USER_EMAILS:
        assign_user_to_fleet(db, email, fleet_id)
    return list(DEMO_USER_EMAILS)
