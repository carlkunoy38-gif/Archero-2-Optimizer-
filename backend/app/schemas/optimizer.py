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
    #: Which `app.optimizer.objectives.ObjectiveProfile` to score
    #: candidates against — "balanced" (default), "boss", "farm", or
    #: "survival". An unknown name is a 404, same as a missing account
    #: or skill id (see `app.optimizer.advisors.skill_advisor.advise_for_account`).
    objective: str = "balanced"


class SkillScoreBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: int
    name: str
    skill_type: SkillType
    score: float
    summary: str
    reasons: list[str]


class SkillAdviceResponse(BaseModel):
    recommended_skill_id: int
    ranking: list[SkillScoreBreakdown]
