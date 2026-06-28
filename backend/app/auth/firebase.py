import logging
from dataclasses import dataclass

import firebase_admin
import jwt
from fastapi import HTTPException, status
from firebase_admin import auth, credentials

from app.config import settings

logger = logging.getLogger(__name__)


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


def _dev_identity_from_token(token: str) -> FirebaseIdentity:
    """Resolve a dev-mode identity from an unverified Firebase ID token.

    AUTH_DISABLED skips signature verification (no admin credentials are
    configured locally), but the frontend still sends a real Firebase ID
    token when a user is signed in. Decoding its claims lets local/dev runs
    resolve the actual logged-in user instead of collapsing everyone onto
    DEV_USER_EMAIL, which would otherwise leak the demo fleet's data to any
    signed-in account.
    """
    dev_identity = FirebaseIdentity(
        firebase_uid="dev-user",
        email=settings.DEV_USER_EMAIL,
        name="Dev User",
    )

    if token == "dev-token":
        return dev_identity

    try:
        claims = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError:
        logger.warning("AUTH_DISABLED: could not decode bearer token, falling back to dev user")
        return dev_identity

    firebase_uid = claims.get("user_id") or claims.get("sub")
    email = claims.get("email")

    if not firebase_uid or not email:
        logger.warning("AUTH_DISABLED: bearer token missing uid/email, falling back to dev user")
        return dev_identity

    return FirebaseIdentity(
        firebase_uid=firebase_uid,
        email=email,
        name=claims.get("name"),
    )


def verify_firebase_token(token: str) -> FirebaseIdentity:
    if settings.AUTH_DISABLED:
        return _dev_identity_from_token(token)

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