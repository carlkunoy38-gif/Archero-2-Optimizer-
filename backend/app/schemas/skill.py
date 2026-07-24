"""Read schema for the Skill catalog endpoint."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import SkillType


class SkillRead(BaseModel):
    """Serialized representation of a `Skill` catalog row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    skill_type: SkillType
    tier: int
    description: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
