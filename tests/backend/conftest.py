"""Shared pytest fixtures for backend tests.

Uses an in-memory SQLite database created fresh per test so tests never
touch the development database file and can run fully in parallel /
in isolation.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import build_engine

# Importing app.domain.models registers every mapped class on
# Base.metadata; without this, create_all() below would create zero
# tables since SQLAlchemy only knows about classes that have been
# imported somewhere in the process.
from app.domain import models  # noqa: F401


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    # build_engine (not a bare create_engine) so tests get the exact same
    # connection setup as the running application — in particular the
    # PRAGMA foreign_keys=ON that app.db.session.enable_sqlite_foreign_keys
    # applies. Without it, tests would validate a laxer database than the
    # one actually deployed.
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()
