from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.firebase import verify_firebase_token
from app.database import get_db
from app.models.user import User
from app.services.user_service import UserService


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if authorization is None:
        from app.config import settings

        if not settings.AUTH_DISABLED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
            )

        token = "dev-token"
    else:
        scheme, _, token = authorization.partition(" ")

        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme",
            )

    identity = verify_firebase_token(token)

    user_service = UserService(db)

    return user_service.get_or_create_user(
        firebase_uid=identity.firebase_uid,
        email=identity.email,
        name=identity.name,
    )


def get_current_fleet_id(
    current_user: User = Depends(get_current_user),
) -> int:
    return current_user.fleet_id