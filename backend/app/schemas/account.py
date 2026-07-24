"""Request/response schemas for the UserAccount endpoint.

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


class AccountCreate(BaseModel):
    """Payload for ``POST /account``."""

    display_name: str = Field(min_length=1, max_length=100)
    gold: int = Field(default=0, ge=0)
    gems: int = Field(default=0, ge=0)
    energy: int = Field(default=0, ge=0)
    combat_power: float = Field(default=0.0, ge=0)
    current_chapter_id: int | None = None


class AccountRead(BaseModel):
    """Serialized representation of a `UserAccount` row."""

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
