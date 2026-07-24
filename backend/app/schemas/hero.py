"""Read schema for the Hero catalog endpoint."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import HeroClass, Rarity


class HeroRead(BaseModel):
    """Serialized representation of a `Hero` catalog row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    hero_class: HeroClass
    rarity: Rarity
    base_hp: float
    base_attack: float
    base_defense: float
    base_attack_speed: float
    signature_skill_description: str | None
    description: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
