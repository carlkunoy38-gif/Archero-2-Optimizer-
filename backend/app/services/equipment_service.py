"""Business logic for the equip/activate actions: the operations that
change which owned item is "the one in use" for a slot or category.

Every function here follows the same shape and the same ordering
requirement: (1) load the target ownership row — 404 if the account
doesn't own that item — (2) clear whatever else currently occupies the
same slot/category for this account, (3) *then* set the target row's
flag. Step 2 must run before step 3: the partial unique index backing
"at most one equipped per account [per slot]" (see docs/architecture.md,
"Equipped-slot rules") would reject the moment two rows are true at
once, so clearing first and setting second is what keeps this
transactional without ever hitting that constraint mid-request. Both
steps commit together in `ownership_repo.save_ownership`'s single
`db.commit()` — nothing here calls `commit()` twice.

Clients never need a separate "unequip the old one" call: that's the
whole point of these actions over the plain ownership update endpoints.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.models import (
    UserAmuletOwnership,
    UserArmorOwnership,
    UserHeroOwnership,
    UserPetOwnership,
    UserRingOwnership,
    UserRuneOwnership,
    UserSkillSelection,
    UserWeaponOwnership,
)
from app.repositories import ownership as ownership_repo

# --- Hero ---------------------------------------------------------------


def activate_hero(db: Session, account_id: int, hero_id: int) -> UserHeroOwnership:
    instance = ownership_repo.get_hero_ownership(db, account_id, hero_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own hero {hero_id}")
    ownership_repo.clear_other_equipped(db, UserHeroOwnership, "is_active", account_id, instance.id)
    instance.is_active = True
    return ownership_repo.save_ownership(db, instance)


def deactivate_hero(db: Session, account_id: int, hero_id: int) -> UserHeroOwnership:
    instance = ownership_repo.get_hero_ownership(db, account_id, hero_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own hero {hero_id}")
    instance.is_active = False
    return ownership_repo.save_ownership(db, instance)


# --- Pet ---------------------------------------------------------------


def activate_pet(db: Session, account_id: int, pet_id: int) -> UserPetOwnership:
    instance = ownership_repo.get_pet_ownership(db, account_id, pet_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own pet {pet_id}")
    ownership_repo.clear_other_equipped(db, UserPetOwnership, "is_active", account_id, instance.id)
    instance.is_active = True
    return ownership_repo.save_ownership(db, instance)


def deactivate_pet(db: Session, account_id: int, pet_id: int) -> UserPetOwnership:
    instance = ownership_repo.get_pet_ownership(db, account_id, pet_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own pet {pet_id}")
    instance.is_active = False
    return ownership_repo.save_ownership(db, instance)


# --- Weapon ---------------------------------------------------------------


def equip_weapon(db: Session, account_id: int, weapon_id: int) -> UserWeaponOwnership:
    instance = ownership_repo.get_weapon_ownership(db, account_id, weapon_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own weapon {weapon_id}")
    ownership_repo.clear_other_equipped(
        db, UserWeaponOwnership, "is_equipped", account_id, instance.id
    )
    instance.is_equipped = True
    return ownership_repo.save_ownership(db, instance)


def unequip_weapon(db: Session, account_id: int, weapon_id: int) -> UserWeaponOwnership:
    instance = ownership_repo.get_weapon_ownership(db, account_id, weapon_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own weapon {weapon_id}")
    instance.is_equipped = False
    return ownership_repo.save_ownership(db, instance)


# --- Armor ---------------------------------------------------------------


def equip_armor(db: Session, account_id: int, armor_id: int) -> UserArmorOwnership:
    instance = ownership_repo.get_armor_ownership(db, account_id, armor_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own armor {armor_id}")
    # Scoped to the same slot: a helmet and a pair of boots may both be
    # equipped at once, so only clear other rows in *this* slot.
    ownership_repo.clear_other_equipped(
        db,
        UserArmorOwnership,
        "is_equipped",
        account_id,
        instance.id,
        UserArmorOwnership.slot == instance.slot,
    )
    instance.is_equipped = True
    return ownership_repo.save_ownership(db, instance)


def unequip_armor(db: Session, account_id: int, armor_id: int) -> UserArmorOwnership:
    instance = ownership_repo.get_armor_ownership(db, account_id, armor_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own armor {armor_id}")
    instance.is_equipped = False
    return ownership_repo.save_ownership(db, instance)


# --- Ring ---------------------------------------------------------------


def equip_ring(db: Session, account_id: int, ring_id: int) -> UserRingOwnership:
    instance = ownership_repo.get_ring_ownership(db, account_id, ring_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own ring {ring_id}")
    ownership_repo.clear_other_equipped(
        db, UserRingOwnership, "is_equipped", account_id, instance.id
    )
    instance.is_equipped = True
    return ownership_repo.save_ownership(db, instance)


def unequip_ring(db: Session, account_id: int, ring_id: int) -> UserRingOwnership:
    instance = ownership_repo.get_ring_ownership(db, account_id, ring_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own ring {ring_id}")
    instance.is_equipped = False
    return ownership_repo.save_ownership(db, instance)


# --- Amulet ---------------------------------------------------------------


def equip_amulet(db: Session, account_id: int, amulet_id: int) -> UserAmuletOwnership:
    instance = ownership_repo.get_amulet_ownership(db, account_id, amulet_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own amulet {amulet_id}")
    ownership_repo.clear_other_equipped(
        db, UserAmuletOwnership, "is_equipped", account_id, instance.id
    )
    instance.is_equipped = True
    return ownership_repo.save_ownership(db, instance)


def unequip_amulet(db: Session, account_id: int, amulet_id: int) -> UserAmuletOwnership:
    instance = ownership_repo.get_amulet_ownership(db, account_id, amulet_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own amulet {amulet_id}")
    instance.is_equipped = False
    return ownership_repo.save_ownership(db, instance)


# --- Rune ---------------------------------------------------------------


def equip_rune(
    db: Session, account_id: int, rune_id: int, socket_index: int
) -> UserRuneOwnership:
    instance = ownership_repo.get_rune_ownership(db, account_id, rune_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own rune {rune_id}")
    # Whichever *other* rune currently sits in this socket gets bumped —
    # this also correctly handles moving `instance` itself from one
    # socket to another, since its own old socket_index is simply
    # overwritten below rather than needing an explicit clear.
    ownership_repo.clear_rune_socket(db, account_id, socket_index, instance.id)
    instance.socket_index = socket_index
    instance.is_equipped = True
    return ownership_repo.save_ownership(db, instance)


def unequip_rune(db: Session, account_id: int, rune_id: int) -> UserRuneOwnership:
    instance = ownership_repo.get_rune_ownership(db, account_id, rune_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} does not own rune {rune_id}")
    instance.is_equipped = False
    instance.socket_index = None
    return ownership_repo.save_ownership(db, instance)


# --- Skill ---------------------------------------------------------------


def equip_skill(
    db: Session, account_id: int, skill_id: int, equipped_slot: int
) -> UserSkillSelection:
    instance = ownership_repo.get_skill_selection(db, account_id, skill_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} has not selected skill {skill_id}")
    if not instance.is_unlocked:
        raise ConflictError(f"Skill {skill_id} is not unlocked and cannot be equipped")
    ownership_repo.clear_skill_slot(db, account_id, equipped_slot, instance.id)
    instance.equipped_slot = equipped_slot
    return ownership_repo.save_ownership(db, instance)


def unequip_skill(db: Session, account_id: int, skill_id: int) -> UserSkillSelection:
    instance = ownership_repo.get_skill_selection(db, account_id, skill_id)
    if instance is None:
        raise NotFoundError(f"Account {account_id} has not selected skill {skill_id}")
    instance.equipped_slot = None
    return ownership_repo.save_ownership(db, instance)
