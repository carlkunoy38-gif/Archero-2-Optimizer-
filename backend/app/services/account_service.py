"""Business logic for account creation, retrieval, and updates."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.models import UserAccount
from app.repositories import account_repository, chapter_repository
from app.schemas.account import AccountCreate, AccountUpdate


def create_account(db: Session, payload: AccountCreate) -> UserAccount:
    if payload.current_chapter_id is not None:
        _require_chapter(db, payload.current_chapter_id)

    account = UserAccount(**payload.model_dump())
    try:
        return account_repository.create_account(db, account)
    except IntegrityError as exc:
        db.rollback()
        if "display_name" in str(exc.orig):
            raise ConflictError(
                f"Display name {payload.display_name!r} is already taken"
            ) from exc
        raise


def get_account(db: Session, account_id: int) -> UserAccount:
    account = account_repository.get_account(db, account_id)
    if account is None:
        raise NotFoundError(f"Account {account_id} not found")
    return account


def get_account_detail(db: Session, account_id: int) -> UserAccount:
    account = account_repository.get_account_with_detail(db, account_id)
    if account is None:
        raise NotFoundError(f"Account {account_id} not found")
    return account


def update_account(db: Session, account_id: int, payload: AccountUpdate) -> UserAccount:
    account = get_account(db, account_id)

    changes = payload.model_dump(exclude_unset=True)
    if "current_chapter_id" in changes and changes["current_chapter_id"] is not None:
        _require_chapter(db, changes["current_chapter_id"])

    for field, value in changes.items():
        setattr(account, field, value)

    return account_repository.save_account(db, account)


def _require_chapter(db: Session, chapter_id: int) -> None:
    if chapter_repository.get_chapter(db, chapter_id) is None:
        raise NotFoundError(f"Chapter {chapter_id} not found")
