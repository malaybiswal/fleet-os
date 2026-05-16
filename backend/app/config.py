from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    API_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    LOG_LEVEL: str = "info"

    # Motive telematics integration (OAuth 2.0)
    MOTIVE_CLIENT_ID: str = ""
    MOTIVE_CLIENT_SECRET: str = ""
    # Access token and refresh token are obtained once via the OAuth authorization
    # code flow and stored here. The client will auto-refresh using the refresh token.
    MOTIVE_ACCESS_TOKEN: str = ""
    MOTIVE_REFRESH_TOKEN: str = ""
    MOTIVE_API_BASE_URL: str = "https://api.gomotive.com"
    MOTIVE_TOKEN_URL: str = "https://api.gomotive.com/oauth/token"

    # Ingestion scheduler
    INGESTION_ENABLED: bool = False
    INGESTION_INTERVAL_MINUTES: int = 5

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
