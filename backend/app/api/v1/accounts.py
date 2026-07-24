"""POST /account"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import account_repository
from app.repositories.errors import ChapterNotFoundError, DuplicateDisplayNameError
from app.schemas.account import AccountCreate, AccountRead

router = APIRouter(prefix="/account", tags=["account"])


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> AccountRead:
    try:
        account = account_repository.create_account(db, payload)
    except DuplicateDisplayNameError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ChapterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AccountRead.model_validate(account)
