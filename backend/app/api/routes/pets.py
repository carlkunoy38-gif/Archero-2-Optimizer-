"""GET /pets, GET /pets/{pet_id}"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import Rarity
from app.schemas.pet import PetRead
from app.services import catalog_service

router = APIRouter(prefix="/pets", tags=["pets"])


@router.get("", response_model=list[PetRead])
def list_pets(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    rarity: Rarity | None = None,
    db: Session = Depends(get_db),
) -> list[PetRead]:
    pets = catalog_service.list_pets(db, limit=limit, offset=offset, rarity=rarity)
    return [PetRead.model_validate(pet) for pet in pets]


@router.get("/{pet_id}", response_model=PetRead)
def get_pet(pet_id: int, db: Session = Depends(get_db)) -> PetRead:
    pet = catalog_service.get_pet(db, pet_id)
    return PetRead.model_validate(pet)
