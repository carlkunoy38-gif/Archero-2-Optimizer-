"""GET /weapons"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import weapon_repository
from app.schemas.weapon import WeaponRead

router = APIRouter(prefix="/weapons", tags=["weapons"])


@router.get("", response_model=list[WeaponRead])
def list_weapons(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[WeaponRead]:
    weapons = weapon_repository.list_weapons(db, limit=limit, offset=offset)
    return [WeaponRead.model_validate(weapon) for weapon in weapons]
