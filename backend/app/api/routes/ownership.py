"""Account ownership sub-resources: POST to own an item, PATCH to update
its progression, DELETE to remove it — for all seven ownership types,
plus skill selection and chapter progress.

Equip/active-flag changes are deliberately *not* here — see
`app/api/routes/equipment.py`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ownership import (
    AmuletOwnershipCreate,
    AmuletOwnershipRead,
    AmuletOwnershipUpdate,
    ArmorOwnershipCreate,
    ArmorOwnershipRead,
    ArmorOwnershipUpdate,
    ChapterProgressRead,
    ChapterProgressUpsert,
    HeroOwnershipCreate,
    HeroOwnershipRead,
    HeroOwnershipUpdate,
    PetOwnershipCreate,
    PetOwnershipRead,
    PetOwnershipUpdate,
    RingOwnershipCreate,
    RingOwnershipRead,
    RingOwnershipUpdate,
    RuneOwnershipCreate,
    RuneOwnershipRead,
    RuneOwnershipUpdate,
    SkillSelectionCreate,
    SkillSelectionRead,
    SkillSelectionUpdate,
    WeaponOwnershipCreate,
    WeaponOwnershipRead,
    WeaponOwnershipUpdate,
)
from app.services import ownership_service

router = APIRouter(prefix="/accounts", tags=["ownership"])


# --- Hero ---------------------------------------------------------------


@router.post(
    "/{account_id}/heroes", response_model=HeroOwnershipRead, status_code=status.HTTP_201_CREATED
)
def create_hero_ownership(
    account_id: int, payload: HeroOwnershipCreate, db: Session = Depends(get_db)
) -> HeroOwnershipRead:
    instance = ownership_service.create_hero_ownership(db, account_id, payload)
    return HeroOwnershipRead.model_validate(instance)


@router.patch("/{account_id}/heroes/{hero_id}", response_model=HeroOwnershipRead)
def update_hero_ownership(
    account_id: int, hero_id: int, payload: HeroOwnershipUpdate, db: Session = Depends(get_db)
) -> HeroOwnershipRead:
    instance = ownership_service.update_hero_ownership(db, account_id, hero_id, payload)
    return HeroOwnershipRead.model_validate(instance)


@router.delete("/{account_id}/heroes/{hero_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hero_ownership(
    account_id: int, hero_id: int, db: Session = Depends(get_db)
) -> None:
    ownership_service.delete_hero_ownership(db, account_id, hero_id)


# --- Weapon ---------------------------------------------------------------


@router.post(
    "/{account_id}/weapons",
    response_model=WeaponOwnershipRead,
    status_code=status.HTTP_201_CREATED,
)
def create_weapon_ownership(
    account_id: int, payload: WeaponOwnershipCreate, db: Session = Depends(get_db)
) -> WeaponOwnershipRead:
    instance = ownership_service.create_weapon_ownership(db, account_id, payload)
    return WeaponOwnershipRead.model_validate(instance)


@router.patch("/{account_id}/weapons/{weapon_id}", response_model=WeaponOwnershipRead)
def update_weapon_ownership(
    account_id: int,
    weapon_id: int,
    payload: WeaponOwnershipUpdate,
    db: Session = Depends(get_db),
) -> WeaponOwnershipRead:
    instance = ownership_service.update_weapon_ownership(db, account_id, weapon_id, payload)
    return WeaponOwnershipRead.model_validate(instance)


@router.delete("/{account_id}/weapons/{weapon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_weapon_ownership(
    account_id: int, weapon_id: int, db: Session = Depends(get_db)
) -> None:
    ownership_service.delete_weapon_ownership(db, account_id, weapon_id)


# --- Armor ---------------------------------------------------------------


@router.post(
    "/{account_id}/armor", response_model=ArmorOwnershipRead, status_code=status.HTTP_201_CREATED
)
def create_armor_ownership(
    account_id: int, payload: ArmorOwnershipCreate, db: Session = Depends(get_db)
) -> ArmorOwnershipRead:
    instance = ownership_service.create_armor_ownership(db, account_id, payload)
    return ArmorOwnershipRead.model_validate(instance)


@router.patch("/{account_id}/armor/{armor_id}", response_model=ArmorOwnershipRead)
def update_armor_ownership(
    account_id: int, armor_id: int, payload: ArmorOwnershipUpdate, db: Session = Depends(get_db)
) -> ArmorOwnershipRead:
    instance = ownership_service.update_armor_ownership(db, account_id, armor_id, payload)
    return ArmorOwnershipRead.model_validate(instance)


@router.delete("/{account_id}/armor/{armor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_armor_ownership(
    account_id: int, armor_id: int, db: Session = Depends(get_db)
) -> None:
    ownership_service.delete_armor_ownership(db, account_id, armor_id)


# --- Ring ---------------------------------------------------------------


@router.post(
    "/{account_id}/rings", response_model=RingOwnershipRead, status_code=status.HTTP_201_CREATED
)
def create_ring_ownership(
    account_id: int, payload: RingOwnershipCreate, db: Session = Depends(get_db)
) -> RingOwnershipRead:
    instance = ownership_service.create_ring_ownership(db, account_id, payload)
    return RingOwnershipRead.model_validate(instance)


@router.patch("/{account_id}/rings/{ring_id}", response_model=RingOwnershipRead)
def update_ring_ownership(
    account_id: int, ring_id: int, payload: RingOwnershipUpdate, db: Session = Depends(get_db)
) -> RingOwnershipRead:
    instance = ownership_service.update_ring_ownership(db, account_id, ring_id, payload)
    return RingOwnershipRead.model_validate(instance)


@router.delete("/{account_id}/rings/{ring_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ring_ownership(account_id: int, ring_id: int, db: Session = Depends(get_db)) -> None:
    ownership_service.delete_ring_ownership(db, account_id, ring_id)


# --- Amulet ---------------------------------------------------------------


@router.post(
    "/{account_id}/amulets",
    response_model=AmuletOwnershipRead,
    status_code=status.HTTP_201_CREATED,
)
def create_amulet_ownership(
    account_id: int, payload: AmuletOwnershipCreate, db: Session = Depends(get_db)
) -> AmuletOwnershipRead:
    instance = ownership_service.create_amulet_ownership(db, account_id, payload)
    return AmuletOwnershipRead.model_validate(instance)


@router.patch("/{account_id}/amulets/{amulet_id}", response_model=AmuletOwnershipRead)
def update_amulet_ownership(
    account_id: int,
    amulet_id: int,
    payload: AmuletOwnershipUpdate,
    db: Session = Depends(get_db),
) -> AmuletOwnershipRead:
    instance = ownership_service.update_amulet_ownership(db, account_id, amulet_id, payload)
    return AmuletOwnershipRead.model_validate(instance)


@router.delete("/{account_id}/amulets/{amulet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_amulet_ownership(
    account_id: int, amulet_id: int, db: Session = Depends(get_db)
) -> None:
    ownership_service.delete_amulet_ownership(db, account_id, amulet_id)


# --- Pet ---------------------------------------------------------------


@router.post(
    "/{account_id}/pets", response_model=PetOwnershipRead, status_code=status.HTTP_201_CREATED
)
def create_pet_ownership(
    account_id: int, payload: PetOwnershipCreate, db: Session = Depends(get_db)
) -> PetOwnershipRead:
    instance = ownership_service.create_pet_ownership(db, account_id, payload)
    return PetOwnershipRead.model_validate(instance)


@router.patch("/{account_id}/pets/{pet_id}", response_model=PetOwnershipRead)
def update_pet_ownership(
    account_id: int, pet_id: int, payload: PetOwnershipUpdate, db: Session = Depends(get_db)
) -> PetOwnershipRead:
    instance = ownership_service.update_pet_ownership(db, account_id, pet_id, payload)
    return PetOwnershipRead.model_validate(instance)


@router.delete("/{account_id}/pets/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pet_ownership(account_id: int, pet_id: int, db: Session = Depends(get_db)) -> None:
    ownership_service.delete_pet_ownership(db, account_id, pet_id)


# --- Rune ---------------------------------------------------------------


@router.post(
    "/{account_id}/runes", response_model=RuneOwnershipRead, status_code=status.HTTP_201_CREATED
)
def create_rune_ownership(
    account_id: int, payload: RuneOwnershipCreate, db: Session = Depends(get_db)
) -> RuneOwnershipRead:
    instance = ownership_service.create_rune_ownership(db, account_id, payload)
    return RuneOwnershipRead.model_validate(instance)


@router.patch("/{account_id}/runes/{rune_id}", response_model=RuneOwnershipRead)
def update_rune_ownership(
    account_id: int, rune_id: int, payload: RuneOwnershipUpdate, db: Session = Depends(get_db)
) -> RuneOwnershipRead:
    instance = ownership_service.update_rune_ownership(db, account_id, rune_id, payload)
    return RuneOwnershipRead.model_validate(instance)


@router.delete("/{account_id}/runes/{rune_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rune_ownership(account_id: int, rune_id: int, db: Session = Depends(get_db)) -> None:
    ownership_service.delete_rune_ownership(db, account_id, rune_id)


# --- Skill selection ------------------------------------------------------


@router.post(
    "/{account_id}/skills",
    response_model=SkillSelectionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_skill_selection(
    account_id: int, payload: SkillSelectionCreate, db: Session = Depends(get_db)
) -> SkillSelectionRead:
    instance = ownership_service.create_skill_selection(db, account_id, payload)
    return SkillSelectionRead.model_validate(instance)


@router.patch("/{account_id}/skills/{skill_id}", response_model=SkillSelectionRead)
def update_skill_selection(
    account_id: int,
    skill_id: int,
    payload: SkillSelectionUpdate,
    db: Session = Depends(get_db),
) -> SkillSelectionRead:
    instance = ownership_service.update_skill_selection(db, account_id, skill_id, payload)
    return SkillSelectionRead.model_validate(instance)


@router.delete("/{account_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill_selection(
    account_id: int, skill_id: int, db: Session = Depends(get_db)
) -> None:
    ownership_service.delete_skill_selection(db, account_id, skill_id)


# --- Chapter progress -------------------------------------------------------


@router.put(
    "/{account_id}/chapters/{chapter_id}/progress",
    response_model=ChapterProgressRead,
)
def upsert_chapter_progress(
    account_id: int,
    chapter_id: int,
    payload: ChapterProgressUpsert,
    db: Session = Depends(get_db),
) -> ChapterProgressRead:
    instance = ownership_service.upsert_chapter_progress(db, account_id, chapter_id, payload)
    return ChapterProgressRead.model_validate(instance)
