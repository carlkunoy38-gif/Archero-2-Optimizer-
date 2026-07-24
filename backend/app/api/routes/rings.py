"""GET /rings, GET /rings/{ring_id}"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import Rarity
from app.schemas.ring import RingRead
from app.services import catalog_service

router = APIRouter(prefix="/rings", tags=["rings"])


@router.get("", response_model=list[RingRead])
def list_rings(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    rarity: Rarity | None = None,
    db: Session = Depends(get_db),
) -> list[RingRead]:
    rings = catalog_service.list_rings(db, limit=limit, offset=offset, rarity=rarity)
    return [RingRead.model_validate(ring) for ring in rings]


@router.get("/{ring_id}", response_model=RingRead)
def get_ring(ring_id: int, db: Session = Depends(get_db)) -> RingRead:
    ring = catalog_service.get_ring(db, ring_id)
    return RingRead.model_validate(ring)
