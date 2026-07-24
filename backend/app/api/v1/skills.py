"""GET /skills"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import skill_repository
from app.schemas.skill import SkillRead

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillRead])
def list_skills(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[SkillRead]:
    skills = skill_repository.list_skills(db, limit=limit, offset=offset)
    return [SkillRead.model_validate(skill) for skill in skills]
