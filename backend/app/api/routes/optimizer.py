"""POST /optimizer/skills/advise — the Skill Advisor endpoint.

Thin wrapper: validates the request shape, delegates to
`app.optimizer.advisors.skill_advisor.advise_for_account`, and reshapes
its `AdvisorResult[Skill]` into the response schema. All of the actual
decision-making lives in `app/optimizer/`, not here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.optimizer.advisors import skill_advisor
from app.schemas.optimizer import SkillAdviceRequest, SkillAdviceResponse, SkillScoreBreakdown

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
