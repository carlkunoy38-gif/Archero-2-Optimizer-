"""Business logic for owning (not equipping — see `equipment_service`)
catalog items: create/update/delete the ownership row that tracks an
account's level/stars/etc. for one hero, weapon, armor piece, ring,
amulet, pet, or rune, plus skill selections and chapter progress.

Every `create_*` function follows the same three steps: confirm the
account exists, confirm the catalog item exists, confirm it isn't
already owned (else `ConflictError`) — then insert. `update_*` and
`delete_*` both start by loading the existing ownership row, raising
`NotFoundError` if there isn't one.

`is_active` / `is_equipped` / `socket_index` / `equipped_slot` are never
set here — only the dedicated actions in `app/services/equipment_service.py`
touch those, since changing them is what triggers the "replace whatever
was equipped before" rule.
"""

from __future__ import annotations

from typing import NoReturn

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.models import (
    UserAmuletOwnership,
    UserArmorOwnership,
    UserChapterProgress,
    UserHeroOwnership,
    UserPetOwnership,
    UserRingOwnership,
    UserRuneOwnership,
    UserSkillSelection,
    UserWeaponOwnership,
)
from app.repositories import ownership as ownership_repo
from app.schemas.ownership import (
    AmuletOwnershipCreate,
    AmuletOwnershipUpdate,
    ArmorOwnershipCreate,
    ArmorOwnershipUpdate,
    ChapterProgressUpsert,
    HeroOwnershipCreate,
    HeroOwnershipUpdate,
    PetOwnershipCreate,
    PetOwnershipUpdate,
    RingOwnershipCreate,
    RingOwnershipUpdate,
    RuneOwnershipCreate,
    RuneOwnershipUpdate,
    SkillSelectionCreate,
    SkillSelectionUpdate,
    WeaponOwnershipCreate,
    WeaponOwnershipUpdate,
)
from app.services import account_service, catalog_service


def _conflict_if_duplicate(exc: IntegrityError, message: str) -> NoReturn:
    """Always raises: `ConflictError` if `exc` looks like the unique
    constraint we expect, otherwise `exc` itself, unmodified — so a
    genuinely unexpected integrity failure surfaces as a 500 (via the
    generic exception handler) rather than being mislabeled as a
    duplicate-ownership conflict."""

    orig_message = str(exc.orig)
    if "UNIQUE constraint failed" in orig_message or "unique constraint" in orig_message.lower():
        raise ConflictError(message) from exc
    raise exc


# --- Hero ---------------------------------------------------------------


def create_hero_ownership(
    db: Session, account_id: int, payload: HeroOwnershipCreate
) -> UserHeroOwnership:
    account_service.get_account(db, account_id)
    catalog_service.get_hero(db, payload.hero_id)
    if ownership_repo.get_hero_ownership(db, account_id, payload.hero_id) is not None:
        raise ConflictError(f"Hero {payload.hero_id} is already owned by this account")

    instance = UserHeroOwnership(
        account_id=account_id, hero_id=payload.hero_id, level=payload.level, stars=payload.stars
    )
    try:
        return ownership_repo.create_hero_ownership(db, instance)
    except IntegrityError as exc:
        db.rollback()
        _conflict_if_duplicate(exc, f"Hero {payload.hero_id} is already owned by this account")


def update_hero_ownership(
    db: Session, account_id: int, hero_id: int, payload: HeroOwnershipUpdate
) -> UserHeroOwnership:
    instance = ownership_repo.get_hero_ownership(db, account_id, hero_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own hero {hero_id}")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)
    return ownership_repo.save_ownership(db, instance)


def delete_hero_ownership(db: Session, account_id: int, hero_id: int) -> None:
    instance = ownership_repo.get_hero_ownership(db, account_id, hero_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own hero {hero_id}")
    ownership_repo.delete_hero_ownership(db, instance)


# --- Weapon ---------------------------------------------------------------


def create_weapon_ownership(
    db: Session, account_id: int, payload: WeaponOwnershipCreate
) -> UserWeaponOwnership:
    account_service.get_account(db, account_id)
    catalog_service.get_weapon(db, payload.weapon_id)
    if ownership_repo.get_weapon_ownership(db, account_id, payload.weapon_id) is not None:
        raise ConflictError(f"Weapon {payload.weapon_id} is already owned by this account")

    instance = UserWeaponOwnership(
        account_id=account_id,
        weapon_id=payload.weapon_id,
        level=payload.level,
        star_level=payload.star_level,
    )
    try:
        return ownership_repo.create_weapon_ownership(db, instance)
    except IntegrityError as exc:
        db.rollback()
        _conflict_if_duplicate(
            exc, f"Weapon {payload.weapon_id} is already owned by this account"
        )


def update_weapon_ownership(
    db: Session, account_id: int, weapon_id: int, payload: WeaponOwnershipUpdate
) -> UserWeaponOwnership:
    instance = ownership_repo.get_weapon_ownership(db, account_id, weapon_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own weapon {weapon_id}")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)
    return ownership_repo.save_ownership(db, instance)


def delete_weapon_ownership(db: Session, account_id: int, weapon_id: int) -> None:
    instance = ownership_repo.get_weapon_ownership(db, account_id, weapon_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own weapon {weapon_id}")
    ownership_repo.delete_weapon_ownership(db, instance)


# --- Armor ---------------------------------------------------------------


def create_armor_ownership(
    db: Session, account_id: int, payload: ArmorOwnershipCreate
) -> UserArmorOwnership:
    account_service.get_account(db, account_id)
    armor = catalog_service.get_armor(db, payload.armor_id)
    if ownership_repo.get_armor_ownership(db, account_id, payload.armor_id) is not None:
        raise ConflictError(f"Armor {payload.armor_id} is already owned by this account")

    # `armor=armor` (not `armor_id=armor.id`) so the `@validates("armor")`
    # hook on UserArmorOwnership copies `armor.slot` automatically — the
    # slot must never be settable from the request (see
    # docs/architecture.md, "Equipped-slot rules").
    instance = UserArmorOwnership(
        account_id=account_id, armor=armor, level=payload.level, star_level=payload.star_level
    )
    try:
        return ownership_repo.create_armor_ownership(db, instance)
    except IntegrityError as exc:
        db.rollback()
        _conflict_if_duplicate(exc, f"Armor {payload.armor_id} is already owned by this account")


def update_armor_ownership(
    db: Session, account_id: int, armor_id: int, payload: ArmorOwnershipUpdate
) -> UserArmorOwnership:
    instance = ownership_repo.get_armor_ownership(db, account_id, armor_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own armor {armor_id}")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)
    return ownership_repo.save_ownership(db, instance)


def delete_armor_ownership(db: Session, account_id: int, armor_id: int) -> None:
    instance = ownership_repo.get_armor_ownership(db, account_id, armor_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own armor {armor_id}")
    ownership_repo.delete_armor_ownership(db, instance)


# --- Ring ---------------------------------------------------------------


def create_ring_ownership(
    db: Session, account_id: int, payload: RingOwnershipCreate
) -> UserRingOwnership:
    account_service.get_account(db, account_id)
    catalog_service.get_ring(db, payload.ring_id)
    if ownership_repo.get_ring_ownership(db, account_id, payload.ring_id) is not None:
        raise ConflictError(f"Ring {payload.ring_id} is already owned by this account")

    instance = UserRingOwnership(
        account_id=account_id, ring_id=payload.ring_id, level=payload.level
    )
    try:
        return ownership_repo.create_ring_ownership(db, instance)
    except IntegrityError as exc:
        db.rollback()
        _conflict_if_duplicate(exc, f"Ring {payload.ring_id} is already owned by this account")


def update_ring_ownership(
    db: Session, account_id: int, ring_id: int, payload: RingOwnershipUpdate
) -> UserRingOwnership:
    instance = ownership_repo.get_ring_ownership(db, account_id, ring_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own ring {ring_id}")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)
    return ownership_repo.save_ownership(db, instance)


def delete_ring_ownership(db: Session, account_id: int, ring_id: int) -> None:
    instance = ownership_repo.get_ring_ownership(db, account_id, ring_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own ring {ring_id}")
    ownership_repo.delete_ring_ownership(db, instance)


# --- Amulet ---------------------------------------------------------------


def create_amulet_ownership(
    db: Session, account_id: int, payload: AmuletOwnershipCreate
) -> UserAmuletOwnership:
    account_service.get_account(db, account_id)
    catalog_service.get_amulet(db, payload.amulet_id)
    if ownership_repo.get_amulet_ownership(db, account_id, payload.amulet_id) is not None:
        raise ConflictError(f"Amulet {payload.amulet_id} is already owned by this account")

    instance = UserAmuletOwnership(
        account_id=account_id, amulet_id=payload.amulet_id, level=payload.level
    )
    try:
        return ownership_repo.create_amulet_ownership(db, instance)
    except IntegrityError as exc:
        db.rollback()
        _conflict_if_duplicate(
            exc, f"Amulet {payload.amulet_id} is already owned by this account"
        )


def update_amulet_ownership(
    db: Session, account_id: int, amulet_id: int, payload: AmuletOwnershipUpdate
) -> UserAmuletOwnership:
    instance = ownership_repo.get_amulet_ownership(db, account_id, amulet_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own amulet {amulet_id}")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)
    return ownership_repo.save_ownership(db, instance)


def delete_amulet_ownership(db: Session, account_id: int, amulet_id: int) -> None:
    instance = ownership_repo.get_amulet_ownership(db, account_id, amulet_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own amulet {amulet_id}")
    ownership_repo.delete_amulet_ownership(db, instance)


# --- Pet ---------------------------------------------------------------


def create_pet_ownership(
    db: Session, account_id: int, payload: PetOwnershipCreate
) -> UserPetOwnership:
    account_service.get_account(db, account_id)
    catalog_service.get_pet(db, payload.pet_id)
    if ownership_repo.get_pet_ownership(db, account_id, payload.pet_id) is not None:
        raise ConflictError(f"Pet {payload.pet_id} is already owned by this account")

    instance = UserPetOwnership(account_id=account_id, pet_id=payload.pet_id, level=payload.level)
    try:
        return ownership_repo.create_pet_ownership(db, instance)
    except IntegrityError as exc:
        db.rollback()
        _conflict_if_duplicate(exc, f"Pet {payload.pet_id} is already owned by this account")


def update_pet_ownership(
    db: Session, account_id: int, pet_id: int, payload: PetOwnershipUpdate
) -> UserPetOwnership:
    instance = ownership_repo.get_pet_ownership(db, account_id, pet_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own pet {pet_id}")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)
    return ownership_repo.save_ownership(db, instance)


def delete_pet_ownership(db: Session, account_id: int, pet_id: int) -> None:
    instance = ownership_repo.get_pet_ownership(db, account_id, pet_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own pet {pet_id}")
    ownership_repo.delete_pet_ownership(db, instance)


# --- Rune ---------------------------------------------------------------


def create_rune_ownership(
    db: Session, account_id: int, payload: RuneOwnershipCreate
) -> UserRuneOwnership:
    account_service.get_account(db, account_id)
    catalog_service.get_rune(db, payload.rune_id)
    if ownership_repo.get_rune_ownership(db, account_id, payload.rune_id) is not None:
        raise ConflictError(f"Rune {payload.rune_id} is already owned by this account")

    instance = UserRuneOwnership(
        account_id=account_id, rune_id=payload.rune_id, level=payload.level
    )
    try:
        return ownership_repo.create_rune_ownership(db, instance)
    except IntegrityError as exc:
        db.rollback()
        _conflict_if_duplicate(exc, f"Rune {payload.rune_id} is already owned by this account")


def update_rune_ownership(
    db: Session, account_id: int, rune_id: int, payload: RuneOwnershipUpdate
) -> UserRuneOwnership:
    instance = ownership_repo.get_rune_ownership(db, account_id, rune_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own rune {rune_id}")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)
    return ownership_repo.save_ownership(db, instance)


def delete_rune_ownership(db: Session, account_id: int, rune_id: int) -> None:
    instance = ownership_repo.get_rune_ownership(db, account_id, rune_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own rune {rune_id}")
    ownership_repo.delete_rune_ownership(db, instance)


# --- Skill selection ------------------------------------------------------


def create_skill_selection(
    db: Session, account_id: int, payload: SkillSelectionCreate
) -> UserSkillSelection:
    account_service.get_account(db, account_id)
    catalog_service.get_skill(db, payload.skill_id)
    if ownership_repo.get_skill_selection(db, account_id, payload.skill_id) is not None:
        raise ConflictError(f"Skill {payload.skill_id} is already selected by this account")

    instance = UserSkillSelection(
        account_id=account_id, skill_id=payload.skill_id, is_unlocked=payload.is_unlocked
    )
    try:
        return ownership_repo.create_skill_selection(db, instance)
    except IntegrityError as exc:
        db.rollback()
        _conflict_if_duplicate(
            exc, f"Skill {payload.skill_id} is already selected by this account"
        )


def update_skill_selection(
    db: Session, account_id: int, skill_id: int, payload: SkillSelectionUpdate
) -> UserSkillSelection:
    instance = ownership_repo.get_skill_selection(db, account_id, skill_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} has not selected skill {skill_id}")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)
    return ownership_repo.save_ownership(db, instance)


def delete_skill_selection(db: Session, account_id: int, skill_id: int) -> None:
    instance = ownership_repo.get_skill_selection(db, account_id, skill_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} has not selected skill {skill_id}")
    ownership_repo.delete_skill_selection(db, instance)


# --- Chapter progress -------------------------------------------------------


def upsert_chapter_progress(
    db: Session, account_id: int, chapter_id: int, payload: ChapterProgressUpsert
) -> UserChapterProgress:
    account_service.get_account(db, account_id)
    catalog_service.get_chapter(db, chapter_id)

    instance = ownership_repo.get_chapter_progress(db, account_id, chapter_id)
    changes = payload.model_dump(exclude_unset=True)

    if instance is None:
        instance = UserChapterProgress(account_id=account_id, chapter_id=chapter_id, **changes)
        return ownership_repo.create_chapter_progress(db, instance)

    for field, value in changes.items():
        setattr(instance, field, value)
    return ownership_repo.save_ownership(db, instance)
