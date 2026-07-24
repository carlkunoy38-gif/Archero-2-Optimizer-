"""GET /runes, GET /runes/{rune_id}"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import Rarity, RuneType
from app.schemas.rune import RuneRead
from app.services import catalog_service

router = APIRouter(prefix="/runes", tags=["runes"])


@router.get("", response_model=list[RuneRead])
def list_runes(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    rarity: Rarity | None = None,
    rune_type: RuneType | None = None,
    db: Session = Depends(get_db),
) -> list[RuneRead]:
    runes = catalog_service.list_runes(
        db, limit=limit, offset=offset, rarity=rarity, rune_type=rune_type
    )
    return [RuneRead.model_validate(rune) for rune in runes]


@router.get("/{rune_id}", response_model=RuneRead)
def get_rune(rune_id: int, db: Session = Depends(get_db)) -> RuneRead:
    rune = catalog_service.get_rune(db, rune_id)
    return RuneRead.model_validate(rune)
