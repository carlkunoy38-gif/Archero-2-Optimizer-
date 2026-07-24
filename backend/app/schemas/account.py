"""Request/response schemas for account endpoints.

Field constraints here (``ge=0`` on resource counts) mirror the
CheckConstraints on `UserAccount` itself (see
`app/domain/models/user_account.py`) so a bad request is rejected with a
422 and a field-level error message before it ever reaches the database
— the database constraint remains the actual guarantee, not the API
layer, but there's no reason to make a client round-trip to the DB
just to learn that gold can't be negative.
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.ownership import (
    AmuletOwnershipRead,
    ArmorOwnershipRead,
    ChapterProgressRead,
    HeroOwnershipRead,
    PetOwnershipRead,
    RingOwnershipRead,
    RuneOwnershipRead,
    SkillSelectionRead,
    WeaponOwnershipRead,
)


class AccountCreate(BaseModel):
    """Payload for ``POST /accounts``."""

    display_name: str = Field(min_length=1, max_length=100)
    gold: int = Field(default=0, ge=0)
    gems: int = Field(default=0, ge=0)
    energy: int = Field(default=0, ge=0)
    combat_power: float = Field(default=0.0, ge=0)
    current_chapter_id: int | None = None


class AccountUpdate(BaseModel):
    """Payload for ``PATCH /accounts/{account_id}``.

    Every field is optional; only fields actually present in the request
    body are applied (see `app/services/account_service.py`, which reads
    this via ``model_dump(exclude_unset=True)``) — so a request that
    explicitly sets ``current_chapter_id: null`` clears it, while simply
    omitting the field leaves it untouched.
    """

    gold: int | None = Field(default=None, ge=0)
    gems: int | None = Field(default=None, ge=0)
    energy: int | None = Field(default=None, ge=0)
    combat_power: float | None = Field(default=None, ge=0)
    current_chapter_id: int | None = None


class AccountRead(BaseModel):
    """Serialized representation of a `UserAccount` row, no nested data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    gold: int
    gems: int
    energy: int
    combat_power: float
    current_chapter_id: int | None
    created_at: dt.datetime
    updated_at: dt.datetime


class AccountDetailRead(AccountRead):
    """`AccountRead` plus every owned item and chapter progress row.

    Returned by ``GET /accounts/{account_id}``. Each nested list uses the
    matching ownership `*Read` schema, which exposes the catalog item's
    id and the account-specific progression/equip state — not the full
    catalog row — matching the ownership-vs-catalog split described in
    `docs/architecture.md`.
    """

    heroes: list[HeroOwnershipRead] = Field(default_factory=list)
    weapons: list[WeaponOwnershipRead] = Field(default_factory=list)
    armor_pieces: list[ArmorOwnershipRead] = Field(default_factory=list)
    rings: list[RingOwnershipRead] = Field(default_factory=list)
    amulets: list[AmuletOwnershipRead] = Field(default_factory=list)
    pets: list[PetOwnershipRead] = Field(default_factory=list)
    runes: list[RuneOwnershipRead] = Field(default_factory=list)
    skill_selections: list[SkillSelectionRead] = Field(default_factory=list)
    chapter_progress: list[ChapterProgressRead] = Field(default_factory=list)
