"""Data access for UserAccount, including account creation."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.models import UserAccount
from app.repositories import chapter_repository
from app.repositories.errors import ChapterNotFoundError, DuplicateDisplayNameError
from app.schemas.account import AccountCreate


def create_account(db: Session, payload: AccountCreate) -> UserAccount:
    """Create a `UserAccount`.

    Raises `ChapterNotFoundError` if `current_chapter_id` is set but no
    such chapter exists, and `DuplicateDisplayNameError` if the display
    name is already taken. Any other integrity violation is re-raised
    as-is rather than mislabeled as one of the above.
    """

    if payload.current_chapter_id is not None:
        chapter = chapter_repository.get_chapter(db, payload.current_chapter_id)
        if chapter is None:
            raise ChapterNotFoundError(payload.current_chapter_id)

    account = UserAccount(**payload.model_dump())
    db.add(account)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "display_name" in str(exc.orig):
            raise DuplicateDisplayNameError(payload.display_name) from exc
        raise
    db.refresh(account)
    return account
