"""Data access for the Rune catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Rarity, Rune, RuneType


def list_runes(
    db: Session,
    *,
    limit: int,
    offset: int,
    rarity: Rarity | None = None,
    rune_type: RuneType | None = None,
) -> list[Rune]:
    stmt = select(Rune).order_by(Rune.id)
    if rarity is not None:
        stmt = stmt.where(Rune.rarity == rarity)
    if rune_type is not None:
        stmt = stmt.where(Rune.rune_type == rune_type)
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_rune(db: Session, rune_id: int) -> Rune | None:
    return db.get(Rune, rune_id)
