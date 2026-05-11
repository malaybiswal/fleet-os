import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routers import telemetry as telemetry_router
from app.routers import trucks as trucks_router
from app.routers import health as health_router
from app.routers import dwell as dwell_router
from app.routers import alerts as alerts_router
from app.routers.health import set_startup_time

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("fleet_os")


# ---------------------------------------------------------------------------
# DB startup retry with exponential backoff (max 30 s)
# ---------------------------------------------------------------------------
def _wait_for_db(timeout: int = 30) -> None:
    deadline = time.time() + timeout
    delay = 1.0
    attempt = 0
    while True:
        attempt += 1
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established (attempt %d)", attempt)
            return
        except Exception as exc:
            remaining = deadline - time.time()
            if remaining <= 0:
                logger.error(
                    "Could not connect to database after %d seconds: %s", timeout, exc
                )
                raise RuntimeError(
                    f"Database unavailable after {timeout}s startup timeout"
                ) from exc
            sleep_for = min(delay, remaining)
            logger.warning(
                "DB not ready (attempt %d), retrying in %.1fs — %s",
                attempt,
                sleep_for,
                exc,
            )
            time.sleep(sleep_for)
            delay = min(delay * 2, 10)  # exponential backoff, cap at 10 s


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    _wait_for_db(timeout=30)
    set_startup_time(time.time())
    logger.info("Fleet OS API started")
    yield
    logger.info("Fleet OS API shutting down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Fleet OS API",
    description="Fleet Operating System — internal trucking operations intelligence dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.time()
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start))

    response = await call_next(request)

    duration_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        "request_id=%s timestamp=%s method=%s path=%s status_code=%d duration_ms=%.2f",
        request_id,
        timestamp,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    # Expose request_id in response headers for tracing
    response.headers["X-Request-ID"] = request_id
    return response


# ---------------------------------------------------------------------------
# Global exception handler — all 4xx/5xx return {"error": "..."}
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc) or "Internal server error"},
    )


from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Flatten validation errors into a readable message
    messages = [
        f"{' -> '.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in errors
    ]
    return JSONResponse(
        status_code=422,
        content={"error": "; ".join(messages)},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health_router.router)
app.include_router(dwell_router.router)
app.include_router(trucks_router.router)
app.include_router(telemetry_router.router)
app.include_router(alerts_router.router)
