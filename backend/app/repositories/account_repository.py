"""Data access for UserAccount.

Pure CRUD, no business rules: existence checks, duplicate-name
handling, and chapter validation all live in
`app/services/account_service.py`.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.models import (
    Rune,
    Skill,
    UserAccount,
    UserAmuletOwnership,
    UserArmorOwnership,
    UserHeroOwnership,
    UserPetOwnership,
    UserRingOwnership,
    UserRuneOwnership,
    UserSkillSelection,
    UserWeaponOwnership,
)


def get_account(db: Session, account_id: int) -> UserAccount | None:
    return db.get(UserAccount, account_id)


def get_account_with_detail(db: Session, account_id: int) -> UserAccount | None:
    """Like `get_account`, but eager-loads every ownership collection —
    plus, one level deeper, each ownership row's own catalog item
    (`UserHeroOwnership.hero`, `UserWeaponOwnership.weapon`, ...) and
    `current_chapter` — so neither the Module 2 detail response nor the
    Module 3 optimizer engine's `BuildContext` builder (which needs the
    catalog rows' base stats, not just the ownership rows) triggers a
    query per relationship.
    """

    stmt = (
        select(UserAccount)
        .where(UserAccount.id == account_id)
        .options(
            selectinload(UserAccount.heroes).selectinload(UserHeroOwnership.hero),
            selectinload(UserAccount.weapons).selectinload(UserWeaponOwnership.weapon),
            selectinload(UserAccount.armor_pieces).selectinload(UserArmorOwnership.armor),
            selectinload(UserAccount.rings).selectinload(UserRingOwnership.ring),
            selectinload(UserAccount.amulets).selectinload(UserAmuletOwnership.amulet),
            selectinload(UserAccount.pets).selectinload(UserPetOwnership.pet),
            selectinload(UserAccount.runes)
            .selectinload(UserRuneOwnership.rune)
            .selectinload(Rune.effects),
            selectinload(UserAccount.skill_selections)
            .selectinload(UserSkillSelection.skill)
            .selectinload(Skill.effects),
            selectinload(UserAccount.chapter_progress),
            selectinload(UserAccount.current_chapter),
        )
    )
    return db.scalars(stmt).one_or_none()


def create_account(db: Session, instance: UserAccount) -> UserAccount:
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def save_account(db: Session, instance: UserAccount) -> UserAccount:
    """Persist in-place changes already applied to `instance` (used by
    account updates, where the service sets attributes before calling
    this)."""

    db.commit()
    db.refresh(instance)
    return instance
