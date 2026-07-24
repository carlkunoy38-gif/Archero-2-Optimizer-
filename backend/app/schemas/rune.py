"""Read schema for the Rune catalog endpoint."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import Rarity, RuneType


class RuneRead(BaseModel):
    """Serialized representation of a `Rune` catalog row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rune_type: RuneType
    rarity: Rarity
    effect_description: str | None
    effect_value: float
    created_at: dt.datetime
    updated_at: dt.datetime
