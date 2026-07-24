"""POST /accounts, GET /accounts/{account_id}, PATCH /accounts/{account_id}"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.account import AccountCreate, AccountDetailRead, AccountRead, AccountUpdate
from app.services import account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> AccountRead:
    account = account_service.create_account(db, payload)
    return AccountRead.model_validate(account)


@router.get("/{account_id}", response_model=AccountDetailRead)
def get_account(account_id: int, db: Session = Depends(get_db)) -> AccountDetailRead:
    account = account_service.get_account_detail(db, account_id)
    return AccountDetailRead.model_validate(account)


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int, payload: AccountUpdate, db: Session = Depends(get_db)
) -> AccountRead:
    account = account_service.update_account(db, account_id, payload)
    return AccountRead.model_validate(account)
