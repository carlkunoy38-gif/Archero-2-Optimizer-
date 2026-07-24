"""Environment-driven application settings.

All configuration is read from environment variables (optionally via a
``.env`` file) so the same codebase can run against SQLite in development
and PostgreSQL in production without code changes.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> parents[3] is the repo root (the parent
# of backend/). Anchoring the default DB path here means it resolves the
# same way regardless of whether uvicorn, alembic, or pytest is launched
# from the repo root or from backend/.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_SQLITE_PATH = _REPO_ROOT / "database" / "archero2.db"


class Settings(BaseSettings):
    """Application settings.

    Values are loaded in this precedence order (highest first):
    explicit constructor args -> environment variables -> ``.env`` file ->
    field defaults below.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ARCHERO_",
        extra="ignore",
    )

    app_name: str = "Archero 2 Optimizer"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)

    # SQLAlchemy connection string. Defaults to a local SQLite file so the
    # project runs with zero external setup. Point this at a PostgreSQL
    # DSN (e.g. "postgresql+psycopg://user:pass@host/db") in production;
    # no application code needs to change because access goes through
    # SQLAlchemy's engine/session abstraction.
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{_DEFAULT_SQLITE_PATH}"
    )

    log_level: str = Field(default="INFO")

    api_v1_prefix: str = "/api/v1"

    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached, process-wide Settings instance.

    Cached via ``lru_cache`` so settings are parsed once and reused,
    while remaining easy to override in tests via
    ``get_settings.cache_clear()``.
    """

    return Settings()
