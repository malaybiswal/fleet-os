from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "firebase_uid": current_user.firebase_uid,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "fleet_id": current_user.fleet_id,
    }