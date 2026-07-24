"""Data access for the Chapter catalog."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Chapter


def list_chapters(db: Session, *, limit: int, offset: int) -> list[Chapter]:
    stmt = select(Chapter).order_by(Chapter.number).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_chapter(db: Session, chapter_id: int) -> Chapter | None:
    return db.get(Chapter, chapter_id)
