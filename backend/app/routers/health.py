import time
from fastapi import APIRouter
from app.database import check_db_connection

router = APIRouter()

# Populated by main.py at startup
_startup_time: float = 0.0


def set_startup_time(t: float) -> None:
    global _startup_time
    _startup_time = t


@router.get("/health", tags=["health"])
def health_check():
    """Return DB connectivity status and API uptime."""
    db_ok = check_db_connection()
    uptime_seconds = round(time.time() - _startup_time, 2) if _startup_time else 0.0
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "uptime_seconds": uptime_seconds,
    }
