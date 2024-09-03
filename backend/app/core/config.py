"""Application configuration settings."""

import os
from typing import List, Optional

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings."""

    # Application info
    PROJECT_NAME: str = "MedScraperAI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Debug mode
    DEBUG: bool = False

    # Database configuration
    DATABASE_URL: Optional[str] = None

    # Redis configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery configuration
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # CORS origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
    ]

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "JSON"

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v):
        """Set default database URL if not provided."""
        if isinstance(v, str):
            return v
        return "postgresql://medscraper:medscraper123@localhost:5432/medscraper_db"

    @validator("CELERY_BROKER_URL", pre=True)
    def assemble_celery_broker(cls, v, values):
        """Set Celery broker URL from Redis URL if not provided."""
        if isinstance(v, str):
            return v
        return values.get("REDIS_URL", "redis://localhost:6379/0")

    @validator("CELERY_RESULT_BACKEND", pre=True)
    def assemble_celery_backend(cls, v, values):
        """Set Celery result backend URL from Redis URL if not provided."""
        if isinstance(v, str):
            return v
        return values.get("REDIS_URL", "redis://localhost:6379/0")

    class Config:
        """Pydantic configuration."""

        case_sensitive = True
        env_file = ".env"


# Create settings instance
settings = Settings()
