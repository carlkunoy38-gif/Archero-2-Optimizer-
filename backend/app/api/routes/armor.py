"""GET /armor, GET /armor/{armor_id}"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import ArmorSlot, Rarity
from app.schemas.armor import ArmorRead
from app.services import catalog_service

router = APIRouter(prefix="/armor", tags=["armor"])


@router.get("", response_model=list[ArmorRead])
def list_armor(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    rarity: Rarity | None = None,
    slot: ArmorSlot | None = None,
    db: Session = Depends(get_db),
) -> list[ArmorRead]:
    armor = catalog_service.list_armor(db, limit=limit, offset=offset, rarity=rarity, slot=slot)
    return [ArmorRead.model_validate(item) for item in armor]


@router.get("/{armor_id}", response_model=ArmorRead)
def get_armor(armor_id: int, db: Session = Depends(get_db)) -> ArmorRead:
    armor = catalog_service.get_armor(db, armor_id)
    return ArmorRead.model_validate(armor)
