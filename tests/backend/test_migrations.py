"""Alembic migration round-trip test.

Runs the real migration chain (upgrade -> downgrade -> upgrade) against
a temp-file SQLite database using Alembic's own Config/command API —
the same code path ``alembic upgrade head`` uses on the command line —
rather than only trusting that ``Base.metadata.create_all()`` (used by
the other tests' in-memory fixture) matches what the migrations
actually produce.

``alembic/env.py`` deliberately ignores whatever URL is set on the
``Config`` object and always sources it from ``app.core.config.Settings``
(see the "Migrations" section of ``docs/architecture.md``) — one place
decides the database URL, for the app and for Alembic alike. So pointing
this test at a temp-file database means going through that same door:
set ``ARCHERO_DATABASE_URL`` and clear the ``lru_cache`` on
``get_settings`` so the new value actually takes effect.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import inspect

from alembic import command
from app.core.config import get_settings
from app.db.session import build_engine

_BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"


def _alembic_config() -> Config:
    config = Config(str(_BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))
    return config


def test_upgrade_downgrade_upgrade_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "migration_test.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("ARCHERO_DATABASE_URL", db_url)
    get_settings.cache_clear()
    try:
        config = _alembic_config()

        command.upgrade(config, "head")

        engine = build_engine(db_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert "user_accounts" in tables
        assert "user_hero_ownership" in tables
        engine.dispose()

        command.downgrade(config, "base")

        engine = build_engine(db_url)
        inspector = inspect(engine)
        remaining_tables = set(inspector.get_table_names()) - {"alembic_version"}
        assert remaining_tables == set()
        engine.dispose()

        # Re-upgrading after a full downgrade must work too — catches
        # migrations that are only safe to run once (e.g. a hardcoded
        # CREATE without IF NOT EXISTS-equivalent Alembic op).
        command.upgrade(config, "head")

        engine = build_engine(db_url)
        inspector = inspect(engine)
        assert "user_accounts" in set(inspector.get_table_names())
        engine.dispose()
    finally:
        # The env var is restored by monkeypatch's own teardown, but the
        # lru_cache on get_settings would otherwise keep pointing at the
        # (now-deleted) temp-file DB for the rest of the test session.
        get_settings.cache_clear()
