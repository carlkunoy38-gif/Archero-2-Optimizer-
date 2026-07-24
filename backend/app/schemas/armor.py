"""Read schema for the Armor catalog endpoint."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import ArmorSlot, Rarity


class ArmorRead(BaseModel):
    """Serialized representation of an `Armor` catalog row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slot: ArmorSlot
    rarity: Rarity
    base_defense: float
    base_hp: float
    special_effect: str | None
    description: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
