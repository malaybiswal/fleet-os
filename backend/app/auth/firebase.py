from dataclasses import dataclass

import firebase_admin
from fastapi import HTTPException, status
from firebase_admin import auth, credentials

from app.config import settings


@dataclass(frozen=True)
class FirebaseIdentity:
    firebase_uid: str
    email: str
    name: str | None = None


def _initialize_firebase_app() -> None:
    if firebase_admin._apps:
        return

    if not (
        settings.FIREBASE_PROJECT_ID
        and settings.FIREBASE_CLIENT_EMAIL
        and settings.FIREBASE_PRIVATE_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase auth is not configured",
        )

    private_key = settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n")

    cred = credentials.Certificate(
        {
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "private_key": private_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )

    firebase_admin.initialize_app(cred)


def verify_firebase_token(token: str) -> FirebaseIdentity:
    if settings.AUTH_DISABLED:
        return FirebaseIdentity(
            firebase_uid="dev-user",
            email=settings.DEV_USER_EMAIL,
            name="Dev User",
        )

    try:
        _initialize_firebase_app()
        decoded_token = auth.verify_id_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
        ) from exc

    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")
    name = decoded_token.get("name")

    if not firebase_uid or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token missing uid or email",
        )

    return FirebaseIdentity(
        firebase_uid=firebase_uid,
        email=email,
        name=name,
    )