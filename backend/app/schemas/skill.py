"""Read schema for the Skill catalog endpoint."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import EffectType, SkillType


class SkillEffectRead(BaseModel):
    """Serialized representation of one `SkillEffect` row."""

    model_config = ConfigDict(from_attributes=True)

    effect_type: EffectType
    value: float


class SkillRead(BaseModel):
    """Serialized representation of a `Skill` catalog row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    skill_type: SkillType
    tier: int
    description: str | None
    effects: list[SkillEffectRead]
    created_at: dt.datetime
    updated_at: dt.datetime
