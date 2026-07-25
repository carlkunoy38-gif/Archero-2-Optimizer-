"""Structured, mechanical effects a rune grants.

See `EffectType` (`app/domain/models/enums.py`) for why this is a
separate one-row-per-effect table rather than a single `effect_value`
column on `Rune` itself: real Archero 2 runes grant several distinct
effects at once (e.g. a rune might grant both `PLANT_DAMAGE_BONUS` and
`ATTACK_BONUS` simultaneously), which one scalar column could never
represent — the same reasoning `SkillEffect` already established for
skills, applied here once rune screenshots showed the same shape.

GAME DATA PLACEHOLDER: this table exists to hold real effect values
sourced from the live game; see `database/seeds/` for what has actually
been seeded versus what remains illustrative.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.models.enums import EffectType
from app.domain.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.rune import Rune


class RuneEffect(TimestampMixin, Base):
    """One mechanical effect (e.g. +10 plant damage) belonging to a `Rune`.

    Owned entirely by its rune — `ondelete="CASCADE"` here is the
    catalog-internal composition case (an effect has no meaning without
    the rune it modifies), not the account-ownership CASCADE pattern
    used elsewhere for `account_id` foreign keys.
    """

    __tablename__ = "rune_effects"
    __table_args__ = (CheckConstraint("value >= 0", name="value_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    rune_id: Mapped[int] = mapped_column(
        ForeignKey("runes.id", ondelete="CASCADE"), index=True
    )
    effect_type: Mapped[EffectType] = mapped_column(Enum(EffectType, name="effect_type"))
    value: Mapped[float] = mapped_column(default=0.0)

    rune: Mapped[Rune] = relationship(back_populates="effects")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"RuneEffect(rune_id={self.rune_id!r}, effect_type={self.effect_type!r})"
