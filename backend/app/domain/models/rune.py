"""Rune catalog model.

GAME DATA PLACEHOLDER: effect values are illustrative.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.models.enums import Rarity, RuneType
from app.domain.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.user_account import UserRuneOwnership


class Rune(TimestampMixin, Base):
    """A socketable rune that grants a passive effect."""

    __tablename__ = "runes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    rune_type: Mapped[RuneType] = mapped_column(Enum(RuneType, name="rune_type"))
    rarity: Mapped[Rarity] = mapped_column(Enum(Rarity, name="rarity_rune"))

    effect_description: Mapped[str | None] = mapped_column(Text, default=None)
    effect_value: Mapped[float] = mapped_column(default=0.0)

    owner_links: Mapped[list[UserRuneOwnership]] = relationship(
        back_populates="rune"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Rune(id={self.id!r}, name={self.name!r})"
