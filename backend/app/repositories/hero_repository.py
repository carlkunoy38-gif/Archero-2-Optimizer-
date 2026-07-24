"""Data access for the Hero catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Hero


def list_heroes(db: Session, *, limit: int, offset: int) -> list[Hero]:
    stmt = select(Hero).order_by(Hero.id).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())
