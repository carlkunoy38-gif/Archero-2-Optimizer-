"""Data access for the seven ownership tables, the skill-selection table,
and chapter progress.

Grouped in one module because the CRUD shape is identical across all of
them: look up one row for (account, catalog item), create, delete. Each
function is a few explicit lines rather than a single generic
"get_ownership(model, fk_name, ...)" helper — a fully dynamic version
would need `getattr`-based column access for the foreign-key filter,
which doesn't type-check cleanly under `mypy --strict` and isn't worth
losing type safety over for something this short.

`clear_other_equipped` is the one genuinely generic piece: every equip
action (`app/services/equipment_service.py`) needs "set this boolean
flag to False on every other row for the account [in this slot]" before
setting it True on the target row, and that really is the same
operation across all seven tables.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

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

# --- Hero ---------------------------------------------------------------


def get_hero_ownership(
    db: Session, account_id: int, hero_id: int
) -> UserHeroOwnership | None:
    stmt = select(UserHeroOwnership).where(
        UserHeroOwnership.account_id == account_id, UserHeroOwnership.hero_id == hero_id
    )
    return db.scalars(stmt).one_or_none()


def create_hero_ownership(db: Session, instance: UserHeroOwnership) -> UserHeroOwnership:
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def delete_hero_ownership(db: Session, instance: UserHeroOwnership) -> None:
    db.delete(instance)
    db.commit()


# --- Weapon ---------------------------------------------------------------


def get_weapon_ownership(
    db: Session, account_id: int, weapon_id: int
) -> UserWeaponOwnership | None:
    stmt = select(UserWeaponOwnership).where(
        UserWeaponOwnership.account_id == account_id,
        UserWeaponOwnership.weapon_id == weapon_id,
    )
    return db.scalars(stmt).one_or_none()


def create_weapon_ownership(db: Session, instance: UserWeaponOwnership) -> UserWeaponOwnership:
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def delete_weapon_ownership(db: Session, instance: UserWeaponOwnership) -> None:
    db.delete(instance)
    db.commit()


# --- Armor ---------------------------------------------------------------


def get_armor_ownership(
    db: Session, account_id: int, armor_id: int
) -> UserArmorOwnership | None:
    stmt = select(UserArmorOwnership).where(
        UserArmorOwnership.account_id == account_id, UserArmorOwnership.armor_id == armor_id
    )
    return db.scalars(stmt).one_or_none()


def create_armor_ownership(db: Session, instance: UserArmorOwnership) -> UserArmorOwnership:
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def delete_armor_ownership(db: Session, instance: UserArmorOwnership) -> None:
    db.delete(instance)
    db.commit()


# --- Ring ---------------------------------------------------------------


def get_ring_ownership(
    db: Session, account_id: int, ring_id: int
) -> UserRingOwnership | None:
    stmt = select(UserRingOwnership).where(
        UserRingOwnership.account_id == account_id, UserRingOwnership.ring_id == ring_id
    )
    return db.scalars(stmt).one_or_none()


def create_ring_ownership(db: Session, instance: UserRingOwnership) -> UserRingOwnership:
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def delete_ring_ownership(db: Session, instance: UserRingOwnership) -> None:
    db.delete(instance)
    db.commit()


# --- Amulet ---------------------------------------------------------------


def get_amulet_ownership(
    db: Session, account_id: int, amulet_id: int
) -> UserAmuletOwnership | None:
    stmt = select(UserAmuletOwnership).where(
        UserAmuletOwnership.account_id == account_id,
        UserAmuletOwnership.amulet_id == amulet_id,
    )
    return db.scalars(stmt).one_or_none()


def create_amulet_ownership(db: Session, instance: UserAmuletOwnership) -> UserAmuletOwnership:
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def delete_amulet_ownership(db: Session, instance: UserAmuletOwnership) -> None:
    db.delete(instance)
    db.commit()


# --- Pet ---------------------------------------------------------------


def get_pet_ownership(db: Session, account_id: int, pet_id: int) -> UserPetOwnership | None:
    stmt = select(UserPetOwnership).where(
        UserPetOwnership.account_id == account_id, UserPetOwnership.pet_id == pet_id
    )
    return db.scalars(stmt).one_or_none()


def create_pet_ownership(db: Session, instance: UserPetOwnership) -> UserPetOwnership:
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def delete_pet_ownership(db: Session, instance: UserPetOwnership) -> None:
    db.delete(instance)
    db.commit()


# --- Rune ---------------------------------------------------------------


def get_rune_ownership(db: Session, account_id: int, rune_id: int) -> UserRuneOwnership | None:
    stmt = select(UserRuneOwnership).where(
        UserRuneOwnership.account_id == account_id, UserRuneOwnership.rune_id == rune_id
    )
    return db.scalars(stmt).one_or_none()


def create_rune_ownership(db: Session, instance: UserRuneOwnership) -> UserRuneOwnership:
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def delete_rune_ownership(db: Session, instance: UserRuneOwnership) -> None:
    db.delete(instance)
    db.commit()


# --- Skill selection ------------------------------------------------------


def get_skill_selection(
    db: Session, account_id: int, skill_id: int
) -> UserSkillSelection | None:
    stmt = select(UserSkillSelection).where(
        UserSkillSelection.account_id == account_id, UserSkillSelection.skill_id == skill_id
    )
    return db.scalars(stmt).one_or_none()


def create_skill_selection(db: Session, instance: UserSkillSelection) -> UserSkillSelection:
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def delete_skill_selection(db: Session, instance: UserSkillSelection) -> None:
    db.delete(instance)
    db.commit()


# --- Chapter progress -------------------------------------------------------


def get_chapter_progress(
    db: Session, account_id: int, chapter_id: int
) -> UserChapterProgress | None:
    stmt = select(UserChapterProgress).where(
        UserChapterProgress.account_id == account_id,
        UserChapterProgress.chapter_id == chapter_id,
    )
    return db.scalars(stmt).one_or_none()


def create_chapter_progress(
    db: Session, instance: UserChapterProgress
) -> UserChapterProgress:
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


# --- Shared save/equip-replacement helpers ---------------------------------


def save_ownership[T](db: Session, instance: T) -> T:
    """Persist in-place attribute changes already applied to `instance`.

    Generic across every ownership/selection/progress type — an update
    is always "the caller already did `setattr`, now commit and
    refresh," regardless of which model it is. Typed generically (PEP
    695 type parameter, not `Any`) purely so callers keep their concrete
    return type instead of tripping `mypy --strict`'s `no-any-return`
    check.
    """

    db.commit()
    db.refresh(instance)
    return instance


def clear_other_equipped(
    db: Session,
    model: type[Any],
    flag_name: str,
    account_id: int,
    keep_id: int,
    *extra_where: Any,
) -> None:
    """Set `flag_name` to False on every row for `account_id` except
    `keep_id` (and matching `extra_where`, e.g. "same armor slot").

    A single bulk `UPDATE`, not a fetch-then-save-each-row loop, so it
    stays inside the caller's transaction without an extra round trip.
    Must run *before* the caller sets the target row's flag to True, or
    the partial unique index enforcing "at most one equipped" will
    reject the moment both rows are true at once.
    """

    column = getattr(model, flag_name)
    stmt = (
        update(model)
        .where(model.account_id == account_id, model.id != keep_id, column.is_(True), *extra_where)
        .values(**{flag_name: False})
    )
    db.execute(stmt)


def clear_rune_socket(db: Session, account_id: int, socket_index: int, exclude_id: int) -> None:
    """Unequip whichever *other* rune currently occupies `socket_index`.

    Runes need both `socket_index` and `is_equipped` cleared together
    (the CHECK constraint on `UserRuneOwnership` requires the two to
    agree — see docs/architecture.md), which is why this isn't just
    another `clear_other_equipped` call.
    """

    stmt = (
        update(UserRuneOwnership)
        .where(
            UserRuneOwnership.account_id == account_id,
            UserRuneOwnership.id != exclude_id,
            UserRuneOwnership.socket_index == socket_index,
        )
        .values(socket_index=None, is_equipped=False)
    )
    db.execute(stmt)


def clear_skill_slot(db: Session, account_id: int, equipped_slot: int, exclude_id: int) -> None:
    """Unequip whichever *other* skill currently occupies `equipped_slot`."""

    stmt = (
        update(UserSkillSelection)
        .where(
            UserSkillSelection.account_id == account_id,
            UserSkillSelection.id != exclude_id,
            UserSkillSelection.equipped_slot == equipped_slot,
        )
        .values(equipped_slot=None)
    )
    db.execute(stmt)
