"""Request/response schemas for `app/api/routes/optimizer.py`.

These wrap `app.optimizer.results.AdvisorResult`/`ScoredOption` — plain
dataclasses, not Pydantic models — into API-serializable shapes.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.models.enums import ArmorSlot, SkillType
from app.optimizer.advisors.gear_advisor import GearCategory
from app.optimizer.advisors.upgrade_advisor import UpgradeCategory


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


class GearAdviceRequest(BaseModel):
    account_id: int
    category: GearCategory
    #: Required (and only meaningful) when `category` is "armor" — armor
    #: pieces only compete against others in the *same* slot, mirroring
    #: how `equipment_service.equip_armor` itself scopes replacement.
    armor_slot: ArmorSlot | None = None
    objective: str = "balanced"

    @model_validator(mode="after")
    def _armor_requires_slot(self) -> GearAdviceRequest:
        if self.category is GearCategory.ARMOR and self.armor_slot is None:
            raise ValueError("armor_slot is required when category is 'armor'")
        return self


class GearScoreBreakdown(BaseModel):
    category: GearCategory
    catalog_id: int
    name: str
    is_currently_equipped: bool
    score: float
    summary: str
    reasons: list[str]


class GearAdviceResponse(BaseModel):
    recommended_catalog_id: int
    ranking: list[GearScoreBreakdown]


class UpgradeAdviceRequest(BaseModel):
    account_id: int
    objective: str = "balanced"


class UpgradeScoreBreakdown(BaseModel):
    category: UpgradeCategory
    #: The account's actual ownership row id — the real, unambiguous
    #: player resource being upgraded. `catalog_id` alone is *not*
    #: unique across categories (a `Hero` row and a `Weapon` row can
    #: both be catalog id 1), since a single Upgrade Advisor response
    #: spans every ownable category at once, unlike Gear Advisor's
    #: single-category ranking.
    ownership_id: int
    catalog_id: int
    name: str
    from_level: int
    to_level: int
    gold_cost: float
    #: Expected percentage improvement to the build's objective score —
    #: the number itself, not just a description of it, since "how much
    #: better" is the whole point of an upgrade recommendation.
    score: float
    summary: str
    reasons: list[str]


class UpgradeRecommendedOption(BaseModel):
    """Unambiguously identifies `ranking[0]` — `(category, ownership_id)`
    together, never `catalog_id` alone, for the same reason
    `UpgradeScoreBreakdown.ownership_id` exists."""

    category: UpgradeCategory
    ownership_id: int
    catalog_id: int


class UpgradeAdviceResponse(BaseModel):
    recommended: UpgradeRecommendedOption
    ranking: list[UpgradeScoreBreakdown]


class ChapterAdviceRequest(BaseModel):
    account_id: int
    #: "farm" ranks chapters by repeatable farming suitability
    #: (safety + energy efficiency); any other objective ranks by
    #: progression suitability (the furthest chapter still safely
    #: reachable) — see `app.optimizer.advisors.chapter_advisor`.
    objective: str = "balanced"


class ChapterScoreBreakdown(BaseModel):
    chapter_id: int
    number: int
    name: str
    score: float
    summary: str
    reasons: list[str]


class ChapterAdviceResponse(BaseModel):
    recommended_chapter_id: int
    ranking: list[ChapterScoreBreakdown]
