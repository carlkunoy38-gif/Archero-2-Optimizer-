"""Hero catalog model.

GAME DATA PLACEHOLDER: base stats below are illustrative starting values,
not datamined figures. Real per-hero base stats and growth curves should
be seeded via ``database/seeds`` once sourced.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.models.enums import HeroClass, Rarity
from app.domain.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.user_account import UserHeroOwnership


class Hero(TimestampMixin, Base):
    """A playable character available in the game's hero roster."""

    __tablename__ = "heroes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hero_class: Mapped[HeroClass] = mapped_column(Enum(HeroClass, name="hero_class"))
    rarity: Mapped[Rarity] = mapped_column(Enum(Rarity, name="rarity_hero"))

    base_hp: Mapped[float] = mapped_column(default=0.0)
    base_attack: Mapped[float] = mapped_column(default=0.0)
    base_defense: Mapped[float] = mapped_column(default=0.0)
    base_attack_speed: Mapped[float] = mapped_column(default=1.0)

    signature_skill_description: Mapped[str | None] = mapped_column(Text, default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    owner_links: Mapped[list[UserHeroOwnership]] = relationship(
        back_populates="hero"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Hero(id={self.id!r}, name={self.name!r}, class={self.hero_class!r})"
