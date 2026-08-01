"""
Centralised application settings loaded from environment variables / .env file.
Uses pydantic-settings for type-safe configuration with full validation.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Runtime environment identifier."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",          # silently drop unknown env vars
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_NAME: str = "CinePilot AI"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENV: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # Comma-separated list of trusted reverse-proxy hostnames
    TRUSTED_HOSTS: List[str] = ["*"]

    # ------------------------------------------------------------------
    # OpenAPI docs visibility
    # Disable in production by setting DOCS_ENABLED=false
    # ------------------------------------------------------------------
    DOCS_ENABLED: bool = True

    # ------------------------------------------------------------------
    # Database (Supabase / PostgreSQL)
    # ------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/cinepilot"

    # Connection pool tuning
    # pool_size  – persistent connections kept open (per process/worker)
    # max_overflow – extra connections allowed above pool_size under burst load
    # pool_timeout – seconds to wait for a connection before raising PoolTimeout
    # pool_recycle – seconds before a connection is replaced (prevents stale TCP)
    # pool_pre_ping – issue "SELECT 1" before handing a connection to the app
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800   # 30 min – below Supabase's 1-hour idle timeout

    # When True, asyncpg will use SSL/TLS for the Supabase connection.
    # Set to False only for local plain-text Postgres instances.
    DB_SSL_REQUIRED: bool = True

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ------------------------------------------------------------------
    # Gemini (Google Generative AI)
    # ------------------------------------------------------------------
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"

    # ------------------------------------------------------------------
    # Google Maps / Places
    # ------------------------------------------------------------------
    GOOGLE_MAPS_API_KEY: str = ""
    GOOGLE_PLACES_API_KEY: str = ""

    # ------------------------------------------------------------------
    # OpenWeather
    # ------------------------------------------------------------------
    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"

    # ------------------------------------------------------------------
    # LangGraph
    # ------------------------------------------------------------------
    LANGGRAPH_RECURSION_LIMIT: int = 50

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"LOG_LEVEL must be one of {valid}, got '{v}'")
        return upper

    @model_validator(mode="after")
    def coerce_debug_log_level(self) -> "Settings":
        """Force LOG_LEVEL to DEBUG whenever DEBUG=true."""
        if self.DEBUG:
            self.LOG_LEVEL = "DEBUG"
        return self

    # ------------------------------------------------------------------
    # Computed helpers
    # ------------------------------------------------------------------

    @property
    def is_production(self) -> bool:
        return self.ENV == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.ENV == Environment.DEVELOPMENT

    @property
    def openapi_url(self) -> str | None:
        """Return None to fully disable OpenAPI schema in production."""
        return "/openapi.json" if self.DOCS_ENABLED else None

    @property
    def docs_url(self) -> str | None:
        return "/docs" if self.DOCS_ENABLED else None

    @property
    def redoc_url(self) -> str | None:
        return "/redoc" if self.DOCS_ENABLED else None


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of application settings."""
    return Settings()


# Module-level singleton for convenient imports across the codebase
settings: Settings = get_settings()
