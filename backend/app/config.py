from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    API_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    LOG_LEVEL: str = "info"

    AUTH_DISABLED: bool = True
    DEV_FLEET_ID: int = 8
    DEV_USER_EMAIL: str = "dev@fleetos.local"

    FIREBASE_PROJECT_ID: str | None = None
    FIREBASE_CLIENT_EMAIL: str | None = None
    FIREBASE_PRIVATE_KEY: str | None = None

    FMCSA_COMPANY_CENSUS_URL: str = (
        "https://data.transportation.gov/resource/az4n-8mr2.json"
    )

    FMCSA_DAILY_DIFF_URL: str = (
        "https://data.transportation.gov/resource/6qg9-x4f8.json"
    )

    FMCSA_PAGE_SIZE: int = 50_000

    SOCRATA_APP_TOKEN: str | None = None

    GEOTAB_DATABASE: str | None = None
    GEOTAB_USERNAME: str | None = None
    GEOTAB_PASSWORD: str | None = None
    GEOTAB_POLL_INTERVAL_SECONDS: int = 10

    CREDENTIAL_ENCRYPTION_KEY: str | None = None

    DAT_BASE_URL: str = "https://api.dat.com"
    DAT_PROVIDER_MODE: str = "mock"
    DAT_POLL_INTERVAL_SECONDS: int = 60
    DAT_RATE_LIMIT_PER_MINUTE: int = 60
    DAT_MAX_RETRIES: int = 3
    DAT_CIRCUIT_BREAKER_THRESHOLD: int = 3
    DAT_CIRCUIT_BREAKER_COOLDOWN_SECONDS: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
