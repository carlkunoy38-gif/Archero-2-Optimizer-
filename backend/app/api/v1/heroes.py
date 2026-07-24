"""GET /heroes"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import hero_repository
from app.schemas.hero import HeroRead

router = APIRouter(prefix="/heroes", tags=["heroes"])


@router.get("", response_model=list[HeroRead])
def list_heroes(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[HeroRead]:
    heroes = hero_repository.list_heroes(db, limit=limit, offset=offset)
    return [HeroRead.model_validate(hero) for hero in heroes]
