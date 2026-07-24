"""Pet catalog model.

GAME DATA PLACEHOLDER: ability descriptions and bonus values are
illustrative.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.models.enums import Rarity, StatType
from app.domain.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.user_account import UserPetOwnership


class Pet(TimestampMixin, Base):
    """A companion that fights alongside the hero and grants passive bonuses."""

    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    rarity: Mapped[Rarity] = mapped_column(Enum(Rarity, name="rarity_pet"))

    bonus_stat: Mapped[StatType] = mapped_column(Enum(StatType, name="stat_type_pet"))
    bonus_stat_value: Mapped[float] = mapped_column(default=0.0)

    ability_description: Mapped[str | None] = mapped_column(Text, default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    owner_links: Mapped[list[UserPetOwnership]] = relationship(
        back_populates="pet"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Pet(id={self.id!r}, name={self.name!r})"
