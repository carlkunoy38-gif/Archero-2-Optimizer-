"""Rune catalog model.

A rune's `rune_type` (offense/defense/utility) is a broad category kept
for filtering (`GET /runes?rune_type=...`); the actual mechanical
effects a rune grants live on `RuneEffect` rows (`effects`), not a
single scalar column, since real runes grant several distinct effects
at once — see `app/domain/models/rune_effect.py`.

GAME DATA PLACEHOLDER: `rarity` values are illustrative; see
`database/seeds/` for which runes have been seeded with real effect
data sourced from the live game versus which remain placeholders.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.models.enums import Rarity, RuneType
from app.domain.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.rune_effect import RuneEffect
    from app.domain.models.user_account import UserRuneOwnership


class Rune(TimestampMixin, Base):
    """A socketable rune that grants one or more passive effects."""

    __tablename__ = "runes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    rune_type: Mapped[RuneType] = mapped_column(Enum(RuneType, name="rune_type"))
    rarity: Mapped[Rarity] = mapped_column(Enum(Rarity, name="rarity_rune"))

    #: Free-text summary of any qualitative ability the rune grants
    #: beyond its numeric `effects` (e.g. "Links deal 10% ATK as Poison
    #: DMG per second") — not fed into scoring, since there is no
    #: numeric field for it yet; see `RuneEffect` for what is.
    effect_description: Mapped[str | None] = mapped_column(Text, default=None)

    owner_links: Mapped[list[UserRuneOwnership]] = relationship(
        back_populates="rune"
    )
    effects: Mapped[list[RuneEffect]] = relationship(
        back_populates="rune", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Rune(id={self.id!r}, name={self.name!r})"
