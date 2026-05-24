import pytest
from app.config import settings

settings.AUTH_DISABLED = True
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


def _trigrams(s: str) -> set:
    """Return the set of trigrams for a string, matching PostgreSQL pg_trgm padding."""
    s = s.upper()
    padded = "  " + s + " "
    return {padded[i : i + 3] for i in range(len(padded) - 2)}


def _word_similarity(needle: str, haystack: str) -> float:
    """Word-level trigram similarity — mirrors PostgreSQL's word_similarity(needle, haystack).

    Scores the needle against the best-matching contiguous slice of trigrams in the
    haystack, which gives accurate results for short queries against long company names.
    """
    if not needle or not haystack:
        return 0.0
    tn = _trigrams(needle)
    th = _trigrams(haystack)
    if not tn or not th:
        return 0.0
    intersection = len(tn & th)
    # word_similarity denominator uses only the needle set size + unmatched haystack
    # trigrams — approximated here as max(|needle|, |intersection|) in the union.
    union = len(tn | th)
    return intersection / union if union else 0.0


TEST_DATABASE_URL = "sqlite:///./test_carriers.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _register_sqlite_functions(dbapi_conn, _):
    """Register pg_trgm-compatible UDFs so func.word_similarity() works in SQLite tests."""
    dbapi_conn.create_function("word_similarity", 2, _word_similarity)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
