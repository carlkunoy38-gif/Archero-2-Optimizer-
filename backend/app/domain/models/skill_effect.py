"""Structured, mechanical effects a skill grants.

See `EffectType` (`app/domain/models/enums.py`) for why this is a
separate one-row-per-effect table rather than columns on `Skill`
itself: it's what lets the Optimizer Engine score two same-tier,
same-category skills differently instead of treating every OFFENSIVE
skill as interchangeable.

GAME DATA PLACEHOLDER: effect values are illustrative.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.models.enums import EffectType
from app.domain.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.skill import Skill


class SkillEffect(TimestampMixin, Base):
    """One mechanical effect (e.g. +1 projectile) belonging to a `Skill`.

    Owned entirely by its skill — `ondelete="CASCADE"` here is the
    catalog-internal composition case (an effect has no meaning without
    the skill it modifies), not the account-ownership CASCADE pattern
    used elsewhere for `account_id` foreign keys.
    """

    __tablename__ = "skill_effects"
    __table_args__ = (CheckConstraint("value >= 0", name="value_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), index=True
    )
    effect_type: Mapped[EffectType] = mapped_column(Enum(EffectType, name="effect_type"))
    value: Mapped[float] = mapped_column(default=0.0)

    skill: Mapped[Skill] = relationship(back_populates="effects")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"SkillEffect(skill_id={self.skill_id!r}, effect_type={self.effect_type!r})"
