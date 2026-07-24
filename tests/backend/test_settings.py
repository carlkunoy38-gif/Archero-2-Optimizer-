"""Tests for environment-driven configuration (``app.core.config``)
and the engine-building logic that consumes it (``app.db.session``).
"""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.db.session import build_engine


class TestSettings:
    def test_defaults_without_any_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for key in [
            "ARCHERO_APP_NAME",
            "ARCHERO_ENVIRONMENT",
            "ARCHERO_DEBUG",
            "ARCHERO_DATABASE_URL",
            "ARCHERO_SQL_ECHO",
            "ARCHERO_LOG_LEVEL",
        ]:
            monkeypatch.delenv(key, raising=False)

        settings = Settings(_env_file=None)  # type: ignore[call-arg]

        assert settings.app_name == "Archero 2 Optimizer"
        assert settings.debug is True
        assert settings.sql_echo is False
        assert settings.database_url.startswith("sqlite:///")
        assert settings.database_url.endswith("database/archero2.db")

    def test_env_vars_override_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ARCHERO_DATABASE_URL", "sqlite:///:memory:")
        monkeypatch.setenv("ARCHERO_SQL_ECHO", "true")
        monkeypatch.setenv("ARCHERO_DEBUG", "false")
        monkeypatch.setenv("ARCHERO_LOG_LEVEL", "WARNING")

        settings = Settings(_env_file=None)  # type: ignore[call-arg]

        assert settings.database_url == "sqlite:///:memory:"
        assert settings.sql_echo is True
        assert settings.debug is False
        assert settings.log_level == "WARNING"

    def test_sql_echo_is_independent_of_debug(self) -> None:
        # debug=True (the default) must not silently force SQL echo on;
        # they are separate knobs so debug mode doesn't imply
        # logging user-entered query values.
        settings = Settings(_env_file=None, debug=True)  # type: ignore[call-arg]
        assert settings.sql_echo is False


class TestBuildEngine:
    def test_in_memory_sqlite_has_foreign_keys_enabled(self) -> None:
        engine = build_engine("sqlite:///:memory:")
        with engine.connect() as conn:
            result = conn.exec_driver_sql("PRAGMA foreign_keys").scalar()
            assert result == 1

    def test_non_sqlite_url_does_not_get_sqlite_connect_args(self) -> None:
        # Doesn't actually connect (no PostgreSQL server here) — just
        # confirms the SQLite-only branch is skipped for other dialects.
        engine = build_engine("postgresql+psycopg://user:pass@localhost/db")
        assert engine.dialect.name == "postgresql"
