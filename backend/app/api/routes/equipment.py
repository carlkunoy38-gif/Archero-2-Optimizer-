"""Equip/activate actions.

Each of these acts on an item the account already owns (created via
`app/api/routes/ownership.py`) and replaces whatever else was
equipped/active in the same slot or category — see
`app/services/equipment_service.py` for the transactional detail.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ownership import (
    AmuletOwnershipRead,
    ArmorOwnershipRead,
    HeroOwnershipRead,
    PetOwnershipRead,
    RingOwnershipRead,
    RuneEquipRequest,
    RuneOwnershipRead,
    SkillEquipRequest,
    SkillSelectionRead,
    WeaponOwnershipRead,
)
from app.services import equipment_service

router = APIRouter(prefix="/accounts", tags=["equipment"])


# --- Hero ---------------------------------------------------------------


@router.post("/{account_id}/heroes/{hero_id}/activate", response_model=HeroOwnershipRead)
def activate_hero(
    account_id: int, hero_id: int, db: Session = Depends(get_db)
) -> HeroOwnershipRead:
    instance = equipment_service.activate_hero(db, account_id, hero_id)
    return HeroOwnershipRead.model_validate(instance)


@router.post("/{account_id}/heroes/{hero_id}/deactivate", response_model=HeroOwnershipRead)
def deactivate_hero(
    account_id: int, hero_id: int, db: Session = Depends(get_db)
) -> HeroOwnershipRead:
    instance = equipment_service.deactivate_hero(db, account_id, hero_id)
    return HeroOwnershipRead.model_validate(instance)


# --- Pet ---------------------------------------------------------------


@router.post("/{account_id}/pets/{pet_id}/activate", response_model=PetOwnershipRead)
def activate_pet(account_id: int, pet_id: int, db: Session = Depends(get_db)) -> PetOwnershipRead:
    instance = equipment_service.activate_pet(db, account_id, pet_id)
    return PetOwnershipRead.model_validate(instance)


@router.post("/{account_id}/pets/{pet_id}/deactivate", response_model=PetOwnershipRead)
def deactivate_pet(
    account_id: int, pet_id: int, db: Session = Depends(get_db)
) -> PetOwnershipRead:
    instance = equipment_service.deactivate_pet(db, account_id, pet_id)
    return PetOwnershipRead.model_validate(instance)


# --- Weapon ---------------------------------------------------------------


@router.post("/{account_id}/weapons/{weapon_id}/equip", response_model=WeaponOwnershipRead)
def equip_weapon(
    account_id: int, weapon_id: int, db: Session = Depends(get_db)
) -> WeaponOwnershipRead:
    instance = equipment_service.equip_weapon(db, account_id, weapon_id)
    return WeaponOwnershipRead.model_validate(instance)


@router.post("/{account_id}/weapons/{weapon_id}/unequip", response_model=WeaponOwnershipRead)
def unequip_weapon(
    account_id: int, weapon_id: int, db: Session = Depends(get_db)
) -> WeaponOwnershipRead:
    instance = equipment_service.unequip_weapon(db, account_id, weapon_id)
    return WeaponOwnershipRead.model_validate(instance)


# --- Armor ---------------------------------------------------------------


@router.post("/{account_id}/armor/{armor_id}/equip", response_model=ArmorOwnershipRead)
def equip_armor(
    account_id: int, armor_id: int, db: Session = Depends(get_db)
) -> ArmorOwnershipRead:
    instance = equipment_service.equip_armor(db, account_id, armor_id)
    return ArmorOwnershipRead.model_validate(instance)


@router.post("/{account_id}/armor/{armor_id}/unequip", response_model=ArmorOwnershipRead)
def unequip_armor(
    account_id: int, armor_id: int, db: Session = Depends(get_db)
) -> ArmorOwnershipRead:
    instance = equipment_service.unequip_armor(db, account_id, armor_id)
    return ArmorOwnershipRead.model_validate(instance)


# --- Ring ---------------------------------------------------------------


@router.post("/{account_id}/rings/{ring_id}/equip", response_model=RingOwnershipRead)
def equip_ring(account_id: int, ring_id: int, db: Session = Depends(get_db)) -> RingOwnershipRead:
    instance = equipment_service.equip_ring(db, account_id, ring_id)
    return RingOwnershipRead.model_validate(instance)


@router.post("/{account_id}/rings/{ring_id}/unequip", response_model=RingOwnershipRead)
def unequip_ring(
    account_id: int, ring_id: int, db: Session = Depends(get_db)
) -> RingOwnershipRead:
    instance = equipment_service.unequip_ring(db, account_id, ring_id)
    return RingOwnershipRead.model_validate(instance)


# --- Amulet ---------------------------------------------------------------


@router.post("/{account_id}/amulets/{amulet_id}/equip", response_model=AmuletOwnershipRead)
def equip_amulet(
    account_id: int, amulet_id: int, db: Session = Depends(get_db)
) -> AmuletOwnershipRead:
    instance = equipment_service.equip_amulet(db, account_id, amulet_id)
    return AmuletOwnershipRead.model_validate(instance)


@router.post("/{account_id}/amulets/{amulet_id}/unequip", response_model=AmuletOwnershipRead)
def unequip_amulet(
    account_id: int, amulet_id: int, db: Session = Depends(get_db)
) -> AmuletOwnershipRead:
    instance = equipment_service.unequip_amulet(db, account_id, amulet_id)
    return AmuletOwnershipRead.model_validate(instance)


# --- Rune ---------------------------------------------------------------


@router.post("/{account_id}/runes/{rune_id}/equip", response_model=RuneOwnershipRead)
def equip_rune(
    account_id: int, rune_id: int, payload: RuneEquipRequest, db: Session = Depends(get_db)
) -> RuneOwnershipRead:
    instance = equipment_service.equip_rune(db, account_id, rune_id, payload.socket_index)
    return RuneOwnershipRead.model_validate(instance)


@router.post("/{account_id}/runes/{rune_id}/unequip", response_model=RuneOwnershipRead)
def unequip_rune(
    account_id: int, rune_id: int, db: Session = Depends(get_db)
) -> RuneOwnershipRead:
    instance = equipment_service.unequip_rune(db, account_id, rune_id)
    return RuneOwnershipRead.model_validate(instance)


# --- Skill ---------------------------------------------------------------


@router.post("/{account_id}/skills/{skill_id}/equip", response_model=SkillSelectionRead)
def equip_skill(
    account_id: int, skill_id: int, payload: SkillEquipRequest, db: Session = Depends(get_db)
) -> SkillSelectionRead:
    instance = equipment_service.equip_skill(db, account_id, skill_id, payload.equipped_slot)
    return SkillSelectionRead.model_validate(instance)


@router.post("/{account_id}/skills/{skill_id}/unequip", response_model=SkillSelectionRead)
def unequip_skill(
    account_id: int, skill_id: int, db: Session = Depends(get_db)
) -> SkillSelectionRead:
    instance = equipment_service.unequip_skill(db, account_id, skill_id)
    return SkillSelectionRead.model_validate(instance)
