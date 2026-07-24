"""Amulet catalog model.

GAME DATA PLACEHOLDER: primary stat values are illustrative.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.models.enums import Rarity, StatType
from app.domain.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.user_account import UserAmuletOwnership


class Amulet(TimestampMixin, Base):
    """An accessory equippable in the amulet slot."""

    __tablename__ = "amulets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    rarity: Mapped[Rarity] = mapped_column(Enum(Rarity, name="rarity_amulet"))

    primary_stat: Mapped[StatType] = mapped_column(Enum(StatType, name="stat_type_amulet"))
    primary_stat_value: Mapped[float] = mapped_column(default=0.0)

    special_effect: Mapped[str | None] = mapped_column(Text, default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    owner_links: Mapped[list[UserAmuletOwnership]] = relationship(
        back_populates="amulet"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Amulet(id={self.id!r}, name={self.name!r})"
