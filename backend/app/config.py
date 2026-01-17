"""Application configuration."""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


def _default_database_url() -> str:
    """Pick a writable default database path for the current environment."""
    if os.getenv("VERCEL"):
        return "sqlite+aiosqlite:////tmp/notesquared.db"
    return "sqlite+aiosqlite:///./notesquared.db"


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
    ]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()
