"""Read schema for the Pet catalog endpoint."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import Rarity, StatType


class PetRead(BaseModel):
    """Serialized representation of a `Pet` catalog row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rarity: Rarity
    bonus_stat: StatType
    bonus_stat_value: float
    ability_description: str | None
    description: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
