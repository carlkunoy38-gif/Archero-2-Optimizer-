"""Skill catalog model.

Represents the in-run skill choices offered while playing (e.g. the
roguelike skill picks between stages), as distinct from hero signature
skills or gear special effects.

GAME DATA PLACEHOLDER: tags and tier values are illustrative.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.models.enums import SkillType
from app.domain.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.skill_effect import SkillEffect
    from app.domain.models.user_account import UserSkillSelection


class Skill(TimestampMixin, Base):
    """An in-run skill choice (offensive, defensive, utility, or movement)."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    skill_type: Mapped[SkillType] = mapped_column(Enum(SkillType, name="skill_type"))
    tier: Mapped[int] = mapped_column(default=1)

    description: Mapped[str | None] = mapped_column(Text, default=None)

    owner_links: Mapped[list[UserSkillSelection]] = relationship(
        back_populates="skill"
    )
    effects: Mapped[list[SkillEffect]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Skill(id={self.id!r}, name={self.name!r})"
