"""Data access for the Weapon catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Rarity, Weapon


def list_weapons(
    db: Session,
    *,
    limit: int,
    offset: int,
    rarity: Rarity | None = None,
    weapon_type: str | None = None,
) -> list[Weapon]:
    stmt = select(Weapon).order_by(Weapon.id)
    if rarity is not None:
        stmt = stmt.where(Weapon.rarity == rarity)
    if weapon_type is not None:
        stmt = stmt.where(Weapon.weapon_type == weapon_type)
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_weapon(db: Session, weapon_id: int) -> Weapon | None:
    return db.get(Weapon, weapon_id)
