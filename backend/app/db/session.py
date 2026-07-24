"""SQLAlchemy engine and session factory.

Kept deliberately thin: one engine per process, one session per request.
Switching from SQLite to PostgreSQL is a one-line change to
``ARCHERO_DATABASE_URL`` — nothing here is SQLite-specific except the
``check_same_thread`` connect arg, which PostgreSQL simply ignores because
it is only applied for ``sqlite://`` URLs.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _build_engine() -> Engine:
    settings = get_settings()
    connect_args: dict[str, object] = {}

    if settings.database_url.startswith("sqlite"):
        # SQLite forbids sharing a connection across threads by default;
        # FastAPI's request handling can hop threads, so this must be
        # disabled. Safe because each request still gets its own Session.
        connect_args["check_same_thread"] = False

        # Ensure the parent directory for a file-based SQLite DB exists
        # (e.g. "sqlite:///./database/archero2.db" -> ./database/).
        db_path = settings.database_url.removeprefix("sqlite:///")
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    return create_engine(
        settings.database_url,
        connect_args=connect_args,
        echo=settings.debug,
        future=True,
    )


engine: Engine = _build_engine()

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped session.

    Usage: ``db: Session = Depends(get_db)`` in a route handler.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
