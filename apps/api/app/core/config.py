from typing import List, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    APP_NAME: str = "FinSight"
    PORT: int = 8000
    DEBUG: bool = False

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    # Database URLs
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/finsight"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/finsight"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Supabase Auth
    SUPABASE_URL: str = "https://mock.supabase.co"
    SUPABASE_ANON_KEY: str = "mock-anon-key"
    SUPABASE_JWT_SECRET: str = "development-secret-for-jwt-signing-finsight-min-32-chars"
    SUPABASE_JWKS_URL: Optional[str] = None

    # LLM Settings
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_API_KEY: str = "mock-key"

    # Jev / TypeSafe AI Settings
    JEV_API_KEY: str = "mock-jev-key"
    JEV_MODEL: str = "jev-v1"
    JEV_HIGH_CONFIDENCE_THRESHOLD: float = 0.80
    JEV_MEDIUM_CONFIDENCE_THRESHOLD: float = 0.50
    JEV_CLAIM_SUPPORTED_THRESHOLD: float = 0.80
    JEV_CLAIM_UNVERIFIED_THRESHOLD: float = 0.50

    # Agent Guardrails (§17)
    MAX_RESEARCH_ITERATIONS: int = 2
    MAX_TOOL_CALLS: int = 25
    RUN_TIMEOUT_SECONDS: int = 300

    # LangSmith / Observability
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "finsight"
    LANGSMITH_TRACING: bool = False

    # Object Storage
    OBJECT_STORAGE_ENDPOINT: str = "http://localhost:9000"
    OBJECT_STORAGE_BUCKET: str = "finsight"
    OBJECT_STORAGE_ACCESS_KEY: str = "minioadmin"
    OBJECT_STORAGE_SECRET_KEY: str = "minioadmin"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


settings = Settings()
