"""Data access for UserAccount.

Pure CRUD, no business rules: existence checks, duplicate-name
handling, and chapter validation all live in
`app/services/account_service.py`.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.models import UserAccount


def get_account(db: Session, account_id: int) -> UserAccount | None:
    return db.get(UserAccount, account_id)


def get_account_with_detail(db: Session, account_id: int) -> UserAccount | None:
    """Like `get_account`, but eager-loads every ownership collection so
    the detail response doesn't trigger a query per relationship."""

    stmt = (
        select(UserAccount)
        .where(UserAccount.id == account_id)
        .options(
            selectinload(UserAccount.heroes),
            selectinload(UserAccount.weapons),
            selectinload(UserAccount.armor_pieces),
            selectinload(UserAccount.rings),
            selectinload(UserAccount.amulets),
            selectinload(UserAccount.pets),
            selectinload(UserAccount.runes),
            selectinload(UserAccount.skill_selections),
            selectinload(UserAccount.chapter_progress),
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
