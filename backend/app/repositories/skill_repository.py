"""Data access for the Skill catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Skill


def list_skills(db: Session, *, limit: int, offset: int) -> list[Skill]:
    stmt = select(Skill).order_by(Skill.id).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())
