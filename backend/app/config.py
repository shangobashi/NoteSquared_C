"""Application configuration."""

import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


def _default_database_url() -> str:
    """Pick a writable default database path for the current environment."""
    if os.getenv("VERCEL"):
        return "sqlite+aiosqlite:////tmp/notesquared.db"
    return "sqlite+aiosqlite:///./notesquared.db"


def _to_async_database_url(url: str) -> str:
    """Convert a sync database URL to an async SQLAlchemy URL when needed."""
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    if url.startswith("sqlite://") and "aiosqlite" not in url:
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


def _default_upload_dir() -> str:
    """Pick a writable upload directory for the current environment."""
    if os.getenv("VERCEL"):
        return "/tmp/uploads"
    return "uploads"


class Settings(BaseSettings):
    """Application settings."""

    # App
    app_name: str = "Note² API"
    debug: bool = True

    # Database
    database_url: str = _default_database_url()

    # Uploads
    upload_dir: str = _default_upload_dir()

    # Auth
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # OpenAI (optional for demo)
    openai_api_key: str = ""

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "https://notesquaredccproto.shangobashi.com",
    ]

    class Config:
        env_file = ".env"

    @property
    def async_database_url(self) -> str:
        """Return an async-compatible database URL."""
        return _to_async_database_url(self.database_url)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()
