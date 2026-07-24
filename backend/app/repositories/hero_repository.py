"""Data access for the Hero catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Hero, HeroClass, Rarity


def list_heroes(
    db: Session,
    *,
    limit: int,
    offset: int,
    rarity: Rarity | None = None,
    hero_class: HeroClass | None = None,
) -> list[Hero]:
    stmt = select(Hero).order_by(Hero.id)
    if rarity is not None:
        stmt = stmt.where(Hero.rarity == rarity)
    if hero_class is not None:
        stmt = stmt.where(Hero.hero_class == hero_class)
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_hero(db: Session, hero_id: int) -> Hero | None:
    return db.get(Hero, hero_id)
