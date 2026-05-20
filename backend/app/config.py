from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    API_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    LOG_LEVEL: str = "info"
    FMCSA_COMPANY_CENSUS_URL: str = (
        "https://data.transportation.gov/resource/az4n-8mr2.json"
    )
    FMCSA_DAILY_DIFF_URL: str = (
        "https://data.transportation.gov/resource/6qg9-x4f8.json"
    )
    FMCSA_PAGE_SIZE: int = 50_000
    SOCRATA_APP_TOKEN: str | None = None

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
