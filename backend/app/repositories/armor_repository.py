"""Data access for the Armor catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Armor, ArmorSlot, Rarity


def list_armor(
    db: Session,
    *,
    limit: int,
    offset: int,
    rarity: Rarity | None = None,
    slot: ArmorSlot | None = None,
) -> list[Armor]:
    stmt = select(Armor).order_by(Armor.id)
    if rarity is not None:
        stmt = stmt.where(Armor.rarity == rarity)
    if slot is not None:
        stmt = stmt.where(Armor.slot == slot)
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_armor(db: Session, armor_id: int) -> Armor | None:
    return db.get(Armor, armor_id)
