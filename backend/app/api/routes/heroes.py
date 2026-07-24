"""GET /heroes, GET /heroes/{hero_id}"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import HeroClass, Rarity
from app.schemas.hero import HeroRead
from app.services import catalog_service

router = APIRouter(prefix="/heroes", tags=["heroes"])


@router.get("", response_model=list[HeroRead])
def list_heroes(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    rarity: Rarity | None = None,
    hero_class: HeroClass | None = None,
    db: Session = Depends(get_db),
) -> list[HeroRead]:
    heroes = catalog_service.list_heroes(
        db, limit=limit, offset=offset, rarity=rarity, hero_class=hero_class
    )
    return [HeroRead.model_validate(hero) for hero in heroes]


@router.get("/{hero_id}", response_model=HeroRead)
def get_hero(hero_id: int, db: Session = Depends(get_db)) -> HeroRead:
    hero = catalog_service.get_hero(db, hero_id)
    return HeroRead.model_validate(hero)
