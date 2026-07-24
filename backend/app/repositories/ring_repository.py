"""Data access for the Ring catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Rarity, Ring


def list_rings(
    db: Session, *, limit: int, offset: int, rarity: Rarity | None = None
) -> list[Ring]:
    stmt = select(Ring).order_by(Ring.id)
    if rarity is not None:
        stmt = stmt.where(Ring.rarity == rarity)
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_ring(db: Session, ring_id: int) -> Ring | None:
    return db.get(Ring, ring_id)
