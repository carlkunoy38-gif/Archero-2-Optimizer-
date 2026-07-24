"""Weapon catalog model.

GAME DATA PLACEHOLDER: weapon types and base damage values are
illustrative; replace with real datamined figures when available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.models.enums import Rarity
from app.domain.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.user_account import UserWeaponOwnership


class Weapon(TimestampMixin, Base):
    """A weapon that can be equipped in the primary weapon slot."""

    __tablename__ = "weapons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    weapon_type: Mapped[str] = mapped_column(String(50))
    rarity: Mapped[Rarity] = mapped_column(Enum(Rarity, name="rarity_weapon"))

    base_damage: Mapped[float] = mapped_column(default=0.0)
    base_attack_speed: Mapped[float] = mapped_column(default=1.0)
    crit_chance_bonus: Mapped[float] = mapped_column(default=0.0)

    special_effect: Mapped[str | None] = mapped_column(Text, default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    owner_links: Mapped[list[UserWeaponOwnership]] = relationship(
        back_populates="weapon"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Weapon(id={self.id!r}, name={self.name!r})"
