"""Shared pytest fixtures for backend tests.

Uses an in-memory SQLite database created fresh per test so tests never
touch the development database file and can run fully in parallel /
in isolation.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base

# Importing app.domain.models registers every mapped class on
# Base.metadata; without this, create_all() below would create zero
# tables since SQLAlchemy only knows about classes that have been
# imported somewhere in the process.
from app.domain import models  # noqa: F401


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()
