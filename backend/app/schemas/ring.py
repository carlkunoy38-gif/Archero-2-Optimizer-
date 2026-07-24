"""Read schema for the Ring catalog endpoint."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import Rarity, StatType


class RingRead(BaseModel):
    """Serialized representation of a `Ring` catalog row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rarity: Rarity
    primary_stat: StatType
    primary_stat_value: float
    special_effect: str | None
    description: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
