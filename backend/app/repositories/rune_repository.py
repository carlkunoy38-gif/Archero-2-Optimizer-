"""Data access for the Rune catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.models import Rarity, Rune, RuneType


def list_runes(
    db: Session,
    *,
    limit: int,
    offset: int,
    rarity: Rarity | None = None,
    rune_type: RuneType | None = None,
) -> list[Rune]:
    stmt = select(Rune).options(selectinload(Rune.effects)).order_by(Rune.id)
    if rarity is not None:
        stmt = stmt.where(Rune.rarity == rarity)
    if rune_type is not None:
        stmt = stmt.where(Rune.rune_type == rune_type)
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_rune(db: Session, rune_id: int) -> Rune | None:
    stmt = select(Rune).where(Rune.id == rune_id).options(selectinload(Rune.effects))
    return db.scalars(stmt).one_or_none()
