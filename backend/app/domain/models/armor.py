"""Armor catalog model.

GAME DATA PLACEHOLDER: base defense/HP values are illustrative.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.models.enums import ArmorSlot, Rarity
from app.domain.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.user_account import UserArmorOwnership


class Armor(TimestampMixin, Base):
    """A piece of armor equippable in one of the four armor slots."""

    __tablename__ = "armor"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    slot: Mapped[ArmorSlot] = mapped_column(Enum(ArmorSlot, name="armor_slot"))
    rarity: Mapped[Rarity] = mapped_column(Enum(Rarity, name="rarity_armor"))

    base_defense: Mapped[float] = mapped_column(default=0.0)
    base_hp: Mapped[float] = mapped_column(default=0.0)

    special_effect: Mapped[str | None] = mapped_column(Text, default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    owner_links: Mapped[list[UserArmorOwnership]] = relationship(
        back_populates="armor"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Armor(id={self.id!r}, name={self.name!r}, slot={self.slot!r})"
