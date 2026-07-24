"""GET /chapters, GET /chapters/{chapter_id}"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chapter import ChapterRead
from app.services import catalog_service

router = APIRouter(prefix="/chapters", tags=["chapters"])


@router.get("", response_model=list[ChapterRead])
def list_chapters(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[ChapterRead]:
    chapters = catalog_service.list_chapters(db, limit=limit, offset=offset)
    return [ChapterRead.model_validate(chapter) for chapter in chapters]


@router.get("/{chapter_id}", response_model=ChapterRead)
def get_chapter(chapter_id: int, db: Session = Depends(get_db)) -> ChapterRead:
    chapter = catalog_service.get_chapter(db, chapter_id)
    return ChapterRead.model_validate(chapter)
