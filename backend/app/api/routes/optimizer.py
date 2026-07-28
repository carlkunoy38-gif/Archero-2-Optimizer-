"""POST /optimizer/skills/advise, /optimizer/gear/advise,
/optimizer/upgrade/advise, /optimizer/chapters/advise — advisor
endpoints.

Thin wrappers: validate the request shape, delegate to the matching
`app.optimizer.advisors.*.advise_for_account`, and reshape its
`AdvisorResult[T]` into the response schema. All of the actual
decision-making lives in `app/optimizer/`, not here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.optimizer.advisors import chapter_advisor, gear_advisor, skill_advisor, upgrade_advisor
from app.schemas.optimizer import (
    ChapterAdviceRequest,
    ChapterAdviceResponse,
    ChapterScoreBreakdown,
    GearAdviceRequest,
    GearAdviceResponse,
    GearScoreBreakdown,
    SkillAdviceRequest,
    SkillAdviceResponse,
    SkillScoreBreakdown,
    UpgradeAdviceRequest,
    UpgradeAdviceResponse,
    UpgradeRecommendedOption,
    UpgradeScoreBreakdown,
)

router = APIRouter(prefix="/optimizer", tags=["optimizer"])


@router.post("/skills/advise", response_model=SkillAdviceResponse)
def advise_skills(
    payload: SkillAdviceRequest, db: Session = Depends(get_db)
) -> SkillAdviceResponse:
    result = skill_advisor.advise_for_account(
        db, payload.account_id, payload.candidate_skill_ids, payload.objective
    )

    ranking = [
        SkillScoreBreakdown(
            skill_id=scored.option.id,
            name=scored.option.name,
            skill_type=scored.option.skill_type,
            score=scored.score,
            summary=scored.summary,
            reasons=list(scored.reasons),
        )
        for scored in result.ranked
    ]

    return SkillAdviceResponse(
        recommended_skill_id=result.recommended.option.id,
        ranking=ranking,
    )


@router.post("/gear/advise", response_model=GearAdviceResponse)
def advise_gear(payload: GearAdviceRequest, db: Session = Depends(get_db)) -> GearAdviceResponse:
    result = gear_advisor.advise_for_account(
        db, payload.account_id, payload.category, payload.armor_slot, payload.objective
    )

    ranking = [
        GearScoreBreakdown(
            category=scored.option.category,
            catalog_id=scored.option.catalog_id,
            name=scored.option.name,
            is_currently_equipped=scored.option.is_currently_equipped,
            score=scored.score,
            summary=scored.summary,
            reasons=list(scored.reasons),
        )
        for scored in result.ranked
    ]

    return GearAdviceResponse(
        recommended_catalog_id=result.recommended.option.catalog_id,
        ranking=ranking,
    )


@router.post("/upgrade/advise", response_model=UpgradeAdviceResponse)
def advise_upgrade(
    payload: UpgradeAdviceRequest, db: Session = Depends(get_db)
) -> UpgradeAdviceResponse:
    result = upgrade_advisor.advise_for_account(db, payload.account_id, payload.objective)

    ranking = [
        UpgradeScoreBreakdown(
            category=scored.option.category,
            ownership_id=scored.option.ownership_id,
            catalog_id=scored.option.catalog_id,
            name=scored.option.name,
            from_level=scored.option.from_level,
            to_level=scored.option.to_level,
            gold_cost=scored.option.gold_cost,
            score=scored.score,
            summary=scored.summary,
            reasons=list(scored.reasons),
        )
        for scored in result.ranked
    ]

    return UpgradeAdviceResponse(
        recommended=UpgradeRecommendedOption(
            category=result.recommended.option.category,
            ownership_id=result.recommended.option.ownership_id,
            catalog_id=result.recommended.option.catalog_id,
        ),
        ranking=ranking,
    )


@router.post("/chapters/advise", response_model=ChapterAdviceResponse)
def advise_chapters(
    payload: ChapterAdviceRequest, db: Session = Depends(get_db)
) -> ChapterAdviceResponse:
    result = chapter_advisor.advise_for_account(db, payload.account_id, payload.objective)

    ranking = [
        ChapterScoreBreakdown(
            chapter_id=scored.option.id,
            number=scored.option.number,
            name=scored.option.name,
            score=scored.score,
            summary=scored.summary,
            reasons=list(scored.reasons),
        )
        for scored in result.ranked
    ]

    return ChapterAdviceResponse(
        recommended_chapter_id=result.recommended.option.id,
        ranking=ranking,
    )
