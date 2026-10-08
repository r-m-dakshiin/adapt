from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "ADAPT-Engine"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_SITE_URL: str = "http://localhost:8000"
    OPENROUTER_SITE_NAME: str = "ADAPT-Engine"
    LLM_PROVIDER: str = "openrouter"
    LLM_MODEL: str = "nvidia/nemotron-3.5-lightning:free"

    NN_LIBRARY_PATH: str = ""

    META_API_BASE: str = "https://graph.facebook.com/v19.0"
    META_ACCESS_TOKEN: str = ""
    GOOGLE_ADS_API_BASE: str = "https://googleads.googleapis.com/v16"
    GOOGLE_ADS_TOKEN: str = ""

    INGEST_INTERVAL_MINUTES: int = 5
    DIAGNOSE_INTERVAL_MINUTES: int = 10


settings = Settings()
