"""Data access for the Pet catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Pet, Rarity


def list_pets(
    db: Session, *, limit: int, offset: int, rarity: Rarity | None = None
) -> list[Pet]:
    stmt = select(Pet).order_by(Pet.id)
    if rarity is not None:
        stmt = stmt.where(Pet.rarity == rarity)
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_pet(db: Session, pet_id: int) -> Pet | None:
    return db.get(Pet, pet_id)
