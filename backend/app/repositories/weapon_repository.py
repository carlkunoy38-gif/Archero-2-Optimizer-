"""Data access for the Weapon catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Weapon


def list_weapons(db: Session, *, limit: int, offset: int) -> list[Weapon]:
    stmt = select(Weapon).order_by(Weapon.id).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())
