"""SQLAlchemy engine and session factory.

Kept deliberately thin: one engine per process, one session per request.
Switching from SQLite to PostgreSQL is a one-line change to
``ARCHERO_DATABASE_URL`` — nothing here is SQLite-specific except the
``check_same_thread`` connect arg and the foreign-key pragma below, both
of which are no-ops for any other dialect.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


def enable_sqlite_foreign_keys(engine: Engine) -> None:
    """Turn on SQLite's foreign-key enforcement for every connection made
    by ``engine``.

    SQLite ships with foreign-key checking OFF by default for backwards
    compatibility. Without this, an ownership row can silently reference
    an account or catalog item that does not exist, and ``ON DELETE``
    rules on the foreign keys are never applied. PostgreSQL enforces
    foreign keys unconditionally, so this only matters for SQLite.
    """

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def build_engine(database_url: str, *, echo: bool = False) -> Engine:
    """Build an engine for ``database_url`` with SQLite-specific setup applied.

    Factored out from the module-level ``engine`` so tests (e.g. an
    Alembic upgrade/downgrade round-trip against a temp-file database)
    can construct an independent engine with identical connection
    behavior to the one the running application uses.
    """

    connect_args: dict[str, object] = {}
    engine_kwargs: dict[str, object] = {}

    if database_url.startswith("sqlite"):
        # FastAPI's request handling can hop threads; each request still
        # gets its own Session, so sharing the underlying connection
        # across threads is safe.
        connect_args["check_same_thread"] = False

        db_path = database_url.removeprefix("sqlite:///")
        is_memory_db = db_path in ("", ":memory:")

        if is_memory_db:
            # SQLAlchemy's default pool for SQLite hands each thread its
            # own connection — fine for a file on disk, but for
            # ":memory:" each connection *is a separate, empty database*.
            # FastAPI runs sync route handlers in a worker thread, so
            # without StaticPool (one connection, shared and reused by
            # every checkout) a test client's request would see a
            # different, table-less database than the one the test set
            # up. Irrelevant for PostgreSQL or a file-based SQLite DB.
            engine_kwargs["poolclass"] = StaticPool
        else:
            # Ensure the parent directory for a file-based SQLite DB
            # exists (e.g. sqlite:////abs/path/database/archero2.db ->
            # .../database/).
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        database_url, connect_args=connect_args, echo=echo, future=True, **engine_kwargs
    )

    if database_url.startswith("sqlite"):
        enable_sqlite_foreign_keys(engine)

    return engine


def _build_default_engine() -> Engine:
    settings = get_settings()
    return build_engine(settings.database_url, echo=settings.sql_echo)


engine: Engine = _build_default_engine()

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
