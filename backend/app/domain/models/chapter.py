"""Chapter (story stage) catalog model.

GAME DATA PLACEHOLDER: recommended power and boss data are illustrative.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.user_account import UserAccount, UserChapterProgress


class Chapter(TimestampMixin, Base):
    """A story-mode chapter used to gauge farming/boss difficulty."""

    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    boss_name: Mapped[str | None] = mapped_column(String(100), default=None)

    recommended_combat_power: Mapped[float] = mapped_column(default=0.0)
    energy_cost: Mapped[int] = mapped_column(default=6)

    rewards_summary: Mapped[str | None] = mapped_column(Text, default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    progress_links: Mapped[list[UserChapterProgress]] = relationship(
        back_populates="chapter"
    )
    accounts_current_here: Mapped[list[UserAccount]] = relationship(
        back_populates="current_chapter"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Chapter(id={self.id!r}, number={self.number!r}, name={self.name!r})"
