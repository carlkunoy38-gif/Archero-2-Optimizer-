"""Data access for the Chapter catalog."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.models import Chapter


def get_chapter(db: Session, chapter_id: int) -> Chapter | None:
    return db.get(Chapter, chapter_id)
