"""Read schema for the Rune catalog endpoint."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import EffectType, Rarity, RuneType


class RuneEffectRead(BaseModel):
    """Serialized representation of one `RuneEffect` row."""

    model_config = ConfigDict(from_attributes=True)

    effect_type: EffectType
    value: float


class RuneRead(BaseModel):
    """Serialized representation of a `Rune` catalog row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rune_type: RuneType
    rarity: Rarity
    effect_description: str | None
    effects: list[RuneEffectRead]
    created_at: dt.datetime
    updated_at: dt.datetime
