"""Data access for the Skill catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.models import Skill, SkillType


def list_skills(
    db: Session, *, limit: int, offset: int, skill_type: SkillType | None = None
) -> list[Skill]:
    stmt = select(Skill).options(selectinload(Skill.effects)).order_by(Skill.id)
    if skill_type is not None:
        stmt = stmt.where(Skill.skill_type == skill_type)
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_skill(db: Session, skill_id: int) -> Skill | None:
    stmt = select(Skill).where(Skill.id == skill_id).options(selectinload(Skill.effects))
    return db.scalars(stmt).one_or_none()
