"""GET /skills, GET /skills/{skill_id}"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import SkillType
from app.schemas.skill import SkillRead
from app.services import catalog_service

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillRead])
def list_skills(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    skill_type: SkillType | None = None,
    db: Session = Depends(get_db),
) -> list[SkillRead]:
    skills = catalog_service.list_skills(db, limit=limit, offset=offset, skill_type=skill_type)
    return [SkillRead.model_validate(skill) for skill in skills]


@router.get("/{skill_id}", response_model=SkillRead)
def get_skill(skill_id: int, db: Session = Depends(get_db)) -> SkillRead:
    skill = catalog_service.get_skill(db, skill_id)
    return SkillRead.model_validate(skill)
