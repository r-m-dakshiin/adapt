from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "DQPS-Engine"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_TABLE_EVENTS: str = "engine_events"
    SUPABASE_TABLE_RECOMMENDATIONS: str = "recommendations"
    SUPABASE_TABLE_EXECUTIONS: str = "executions"
    SUPABASE_TABLE_FEEDBACK: str = "outcome_feedback"
    # In the Settings class, add:
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_SITE_URL: str = "http://localhost:8000"
    OPENROUTER_SITE_NAME: str = "DQPS-Engine"

    
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-flash"

    NN_LIBRARY_PATH: str = ""

    META_API_BASE: str = "https://graph.facebook.com/v19.0"
    META_ACCESS_TOKEN: str = ""
    GOOGLE_ADS_API_BASE: str = "https://googleads.googleapis.com/v16"
    GOOGLE_ADS_TOKEN: str = ""

    INGEST_INTERVAL_MINUTES: int = 5
    DIAGNOSE_INTERVAL_MINUTES: int = 10


settings = Settings()
