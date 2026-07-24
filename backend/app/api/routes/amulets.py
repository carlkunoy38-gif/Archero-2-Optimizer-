"""GET /amulets, GET /amulets/{amulet_id}"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import Rarity
from app.schemas.amulet import AmuletRead
from app.services import catalog_service

router = APIRouter(prefix="/amulets", tags=["amulets"])


@router.get("", response_model=list[AmuletRead])
def list_amulets(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    rarity: Rarity | None = None,
    db: Session = Depends(get_db),
) -> list[AmuletRead]:
    amulets = catalog_service.list_amulets(db, limit=limit, offset=offset, rarity=rarity)
    return [AmuletRead.model_validate(amulet) for amulet in amulets]


@router.get("/{amulet_id}", response_model=AmuletRead)
def get_amulet(amulet_id: int, db: Session = Depends(get_db)) -> AmuletRead:
    amulet = catalog_service.get_amulet(db, amulet_id)
    return AmuletRead.model_validate(amulet)
