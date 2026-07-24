"""Request/response schemas for account ownership sub-resources.

Field constraints (`ge=1` on `level`, `ge=0` on the rest) mirror the
CheckConstraints on the matching ORM model
(`app/domain/models/user_account.py`) for the same reason as
`app/schemas/account.py`: a bad request gets a 422 with a field-level
message before it ever reaches the database.

Deliberately absent from every `*Create`/`*Update` schema: the
equip/active flags (`is_active`, `is_equipped`) and slot-position fields
(`socket_index`, `equipped_slot`, and — critically — `Armor`'s `slot`).
Those only change through the dedicated equipment actions
(`app/api/routes/equipment.py`), which enforce the "equipping something
new replaces whatever was there" rule. Letting the generic
create/update endpoints touch them would let a client bypass that rule
and hit the partial-unique-index violation described in
`docs/architecture.md` ("Equipped-slot rules") directly, as a raw 500,
instead of going through the endpoint built to handle it.
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.enums import ArmorSlot

# --- Hero ---------------------------------------------------------------


class HeroOwnershipCreate(BaseModel):
    hero_id: int
    level: int = Field(default=1, ge=1)
    stars: int = Field(default=0, ge=0)


class HeroOwnershipUpdate(BaseModel):
    level: int | None = Field(default=None, ge=1)
    stars: int | None = Field(default=None, ge=0)


class HeroOwnershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hero_id: int
    level: int
    stars: int
    is_active: bool
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Weapon ---------------------------------------------------------------


class WeaponOwnershipCreate(BaseModel):
    weapon_id: int
    level: int = Field(default=1, ge=1)
    star_level: int = Field(default=0, ge=0)


class WeaponOwnershipUpdate(BaseModel):
    level: int | None = Field(default=None, ge=1)
    star_level: int | None = Field(default=None, ge=0)


class WeaponOwnershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    weapon_id: int
    level: int
    star_level: int
    is_equipped: bool
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Armor ---------------------------------------------------------------


class ArmorOwnershipCreate(BaseModel):
    armor_id: int
    level: int = Field(default=1, ge=1)
    star_level: int = Field(default=0, ge=0)


class ArmorOwnershipUpdate(BaseModel):
    level: int | None = Field(default=None, ge=1)
    star_level: int | None = Field(default=None, ge=0)


class ArmorOwnershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    armor_id: int
    slot: ArmorSlot
    level: int
    star_level: int
    is_equipped: bool
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Ring ---------------------------------------------------------------


class RingOwnershipCreate(BaseModel):
    ring_id: int
    level: int = Field(default=1, ge=1)


class RingOwnershipUpdate(BaseModel):
    level: int | None = Field(default=None, ge=1)


class RingOwnershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ring_id: int
    level: int
    is_equipped: bool
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Amulet ---------------------------------------------------------------


class AmuletOwnershipCreate(BaseModel):
    amulet_id: int
    level: int = Field(default=1, ge=1)


class AmuletOwnershipUpdate(BaseModel):
    level: int | None = Field(default=None, ge=1)


class AmuletOwnershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amulet_id: int
    level: int
    is_equipped: bool
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Pet ---------------------------------------------------------------


class PetOwnershipCreate(BaseModel):
    pet_id: int
    level: int = Field(default=1, ge=1)


class PetOwnershipUpdate(BaseModel):
    level: int | None = Field(default=None, ge=1)


class PetOwnershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pet_id: int
    level: int
    is_active: bool
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Rune ---------------------------------------------------------------


class RuneOwnershipCreate(BaseModel):
    rune_id: int
    level: int = Field(default=1, ge=1)


class RuneOwnershipUpdate(BaseModel):
    level: int | None = Field(default=None, ge=1)


class RuneOwnershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rune_id: int
    level: int
    is_equipped: bool
    socket_index: int | None
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Skill selection ------------------------------------------------------


class SkillSelectionCreate(BaseModel):
    skill_id: int
    is_unlocked: bool = False


class SkillSelectionUpdate(BaseModel):
    is_unlocked: bool | None = None


class SkillSelectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    skill_id: int
    is_unlocked: bool
    equipped_slot: int | None
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Chapter progress -------------------------------------------------------


class ChapterProgressUpsert(BaseModel):
    stars_earned: int | None = Field(default=None, ge=0)
    cleared: bool | None = None
    attempts: int | None = Field(default=None, ge=0)


class ChapterProgressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_id: int
    stars_earned: int
    cleared: bool
    attempts: int
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Equipment action request bodies --------------------------------------


class RuneEquipRequest(BaseModel):
    socket_index: int = Field(ge=0)


class SkillEquipRequest(BaseModel):
    equipped_slot: int = Field(ge=0)
