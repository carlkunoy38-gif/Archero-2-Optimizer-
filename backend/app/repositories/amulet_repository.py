"""Data access for the Amulet catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Amulet, Rarity


def list_amulets(
    db: Session, *, limit: int, offset: int, rarity: Rarity | None = None
) -> list[Amulet]:
    stmt = select(Amulet).order_by(Amulet.id)
    if rarity is not None:
        stmt = stmt.where(Amulet.rarity == rarity)
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_amulet(db: Session, amulet_id: int) -> Amulet | None:
    return db.get(Amulet, amulet_id)
