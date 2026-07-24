"""Read schema for the Weapon catalog endpoint."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import Rarity


class WeaponRead(BaseModel):
    """Serialized representation of a `Weapon` catalog row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    weapon_type: str
    rarity: Rarity
    base_damage: float
    base_attack_speed: float
    crit_chance_bonus: float
    special_effect: str | None
    description: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
