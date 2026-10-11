"""
Application configuration using Pydantic Settings.

All configuration is driven by environment variables (loaded from .env).
Never hard-code credentials or secrets.
"""

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, computed_field

# Project root is two levels up from this file: backend/app/config.py -> NLP/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings, loaded from environment variables."""

    # ── Environment ───────────────────────────────────────────────────────
    ENVIRONMENT: str = Field(default="development", description="development | staging | production")
    DEBUG: bool = Field(default=True)
    APP_NAME: str = Field(default="Welfare Awareness Gap Miner")
    APP_VERSION: str = Field(default="0.1.0")

    # ── Database ──────────────────────────────────────────────────────────
    # Primary: PostgreSQL via DATABASE_URL
    # Fallback: SQLite for local development if DATABASE_URL is not set
    DATABASE_URL: str = Field(
        default="sqlite:///./welfare_awareness.db",
        description="PostgreSQL connection string (or SQLite for dev fallback)"
    )

    # ── Security ──────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for token signing. MUST be changed in production."
    )
    API_KEY: str = Field(
        default="",
        description="Optional API key for admin endpoints."
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated allowed origins"
    )

    # ── Frontend ──────────────────────────────────────────────────────────
    NEXT_PUBLIC_API_URL: str = Field(
        default="http://localhost:8000",
        description="Backend URL as seen by the frontend"
    )

    # ── NLP ───────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = Field(
        default="all-MiniLM-L6-v2",
        description="SentenceTransformer model name"
    )
    EMBEDDING_DIMENSION: int = Field(default=384)
    NLP_BATCH_SIZE: int = Field(default=100)

    # ── File uploads ──────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = Field(default=50)
    UPLOAD_DIR: str = Field(default="data/uploads")
    ALLOWED_EXTENSIONS: str = Field(default=".csv,.json,.xlsx")

    # ── Scraping ──────────────────────────────────────────────────────────
    SCRAPER_USER_AGENT: str = Field(
        default="WelfareAwarenessResearchBot/0.1 (+academic-research)",
        description="User-Agent for web collection requests"
    )
    SCRAPER_DEFAULT_DELAY: float = Field(default=2.0, description="Default seconds between requests")
    SCRAPER_DEFAULT_TIMEOUT: int = Field(default=30, description="Default request timeout in seconds")
    SCRAPER_MAX_RETRIES: int = Field(default=3)

    # ── Paths ─────────────────────────────────────────────────────────────
    DATA_DIR: str = Field(default="data")
    MODELS_DIR: str = Field(default="data/models")
    LOGS_DIR: str = Field(default="logs")

    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @computed_field
    @property
    def allowed_extension_list(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()]

    @computed_field
    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
