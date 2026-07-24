"""Request/response schemas for `app/api/routes/optimizer.py`.

These wrap `app.optimizer.results.AdvisorResult`/`ScoredOption` — plain
dataclasses, not Pydantic models — into API-serializable shapes.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.enums import SkillType


class SkillAdviceRequest(BaseModel):
    account_id: int
    candidate_skill_ids: list[int] = Field(min_length=1)


class SkillScoreBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: int
    name: str
    skill_type: SkillType
    score: float
    reasons: list[str]


class SkillAdviceResponse(BaseModel):
    recommended_skill_id: int
    ranking: list[SkillScoreBreakdown]
