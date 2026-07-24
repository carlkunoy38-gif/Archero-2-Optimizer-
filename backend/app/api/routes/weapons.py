"""GET /weapons, GET /weapons/{weapon_id}"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import Rarity
from app.schemas.weapon import WeaponRead
from app.services import catalog_service

router = APIRouter(prefix="/weapons", tags=["weapons"])


@router.get("", response_model=list[WeaponRead])
def list_weapons(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    rarity: Rarity | None = None,
    weapon_type: str | None = None,
    db: Session = Depends(get_db),
) -> list[WeaponRead]:
    weapons = catalog_service.list_weapons(
        db, limit=limit, offset=offset, rarity=rarity, weapon_type=weapon_type
    )
    return [WeaponRead.model_validate(weapon) for weapon in weapons]


@router.get("/{weapon_id}", response_model=WeaponRead)
def get_weapon(weapon_id: int, db: Session = Depends(get_db)) -> WeaponRead:
    weapon = catalog_service.get_weapon(db, weapon_id)
    return WeaponRead.model_validate(weapon)
