"""Declarative base shared by every ORM model.

A single ``Base`` must be imported by all model modules and by Alembic's
``env.py`` so that ``Base.metadata`` reflects the entire schema. The naming
convention below gives constraints and indexes deterministic names, which
Alembic needs to autogenerate reliable "add/drop constraint" migrations
(SQLite and PostgreSQL otherwise name them differently or not at all).
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all ORM models in the application."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
