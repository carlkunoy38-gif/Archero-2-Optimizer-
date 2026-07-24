"""Read schema for the Chapter catalog endpoint."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class ChapterRead(BaseModel):
    """Serialized representation of a `Chapter` catalog row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    name: str
    boss_name: str | None
    recommended_combat_power: float
    energy_cost: int
    rewards_summary: str | None
    description: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
