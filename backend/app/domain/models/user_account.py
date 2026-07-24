"""UserAccount and the ownership/progress tables linking it to the catalog.

Design decision: catalog tables (Hero, Weapon, Armor, ...) describe static
game data shared by every player. A player's personal progress on a given
item (level, stars, whether it is currently equipped) is player-specific
and changes constantly, so it does not belong on the catalog row itself.
Each ``User<Item>Ownership`` table is a many-to-many association *with
extra columns* between ``UserAccount`` and one catalog table — the
standard SQLAlchemy "association object" pattern. This keeps the catalog
immutable/shared while letting each account track its own gear state,
and it is why the task's ten requested models expand into a few more
tables under the hood: they are relationship plumbing, not new game
concepts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.amulet import Amulet
    from app.domain.models.armor import Armor
    from app.domain.models.chapter import Chapter
    from app.domain.models.hero import Hero
    from app.domain.models.pet import Pet
    from app.domain.models.ring import Ring
    from app.domain.models.rune import Rune
    from app.domain.models.skill import Skill
    from app.domain.models.weapon import Weapon


class UserAccount(TimestampMixin, Base):
    """A player's account: resources, progress, and owned items."""

    __tablename__ = "user_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    gold: Mapped[int] = mapped_column(default=0)
    gems: Mapped[int] = mapped_column(default=0)
    energy: Mapped[int] = mapped_column(default=0)
    combat_power: Mapped[float] = mapped_column(default=0.0)

    current_chapter_id: Mapped[int | None] = mapped_column(
        ForeignKey("chapters.id"), default=None
    )
    current_chapter: Mapped[Chapter | None] = relationship(
        back_populates="accounts_current_here", foreign_keys=[current_chapter_id]
    )

    heroes: Mapped[list[UserHeroOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    weapons: Mapped[list[UserWeaponOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    armor_pieces: Mapped[list[UserArmorOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    rings: Mapped[list[UserRingOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    amulets: Mapped[list[UserAmuletOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    pets: Mapped[list[UserPetOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    runes: Mapped[list[UserRuneOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    skill_selections: Mapped[list[UserSkillSelection]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    chapter_progress: Mapped[list[UserChapterProgress]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        foreign_keys="UserChapterProgress.account_id",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"UserAccount(id={self.id!r}, display_name={self.display_name!r})"


class UserHeroOwnership(TimestampMixin, Base):
    """A hero owned by an account, with account-specific progression."""

    __tablename__ = "user_hero_ownership"
    __table_args__ = (UniqueConstraint("account_id", "hero_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), index=True)
    hero_id: Mapped[int] = mapped_column(ForeignKey("heroes.id"), index=True)

    level: Mapped[int] = mapped_column(default=1)
    stars: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[UserAccount] = relationship(back_populates="heroes")
    hero: Mapped[Hero] = relationship(back_populates="owner_links")


class UserWeaponOwnership(TimestampMixin, Base):
    """A weapon owned by an account, with account-specific progression."""

    __tablename__ = "user_weapon_ownership"
    __table_args__ = (UniqueConstraint("account_id", "weapon_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), index=True)
    weapon_id: Mapped[int] = mapped_column(ForeignKey("weapons.id"), index=True)

    level: Mapped[int] = mapped_column(default=1)
    star_level: Mapped[int] = mapped_column(default=0)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[UserAccount] = relationship(back_populates="weapons")
    weapon: Mapped[Weapon] = relationship(back_populates="owner_links")


class UserArmorOwnership(TimestampMixin, Base):
    """An armor piece owned by an account, with account-specific progression."""

    __tablename__ = "user_armor_ownership"
    __table_args__ = (UniqueConstraint("account_id", "armor_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), index=True)
    armor_id: Mapped[int] = mapped_column(ForeignKey("armor.id"), index=True)

    level: Mapped[int] = mapped_column(default=1)
    star_level: Mapped[int] = mapped_column(default=0)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[UserAccount] = relationship(back_populates="armor_pieces")
    armor: Mapped[Armor] = relationship(back_populates="owner_links")


class UserRingOwnership(TimestampMixin, Base):
    """A ring owned by an account, with account-specific progression."""

    __tablename__ = "user_ring_ownership"
    __table_args__ = (UniqueConstraint("account_id", "ring_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), index=True)
    ring_id: Mapped[int] = mapped_column(ForeignKey("rings.id"), index=True)

    level: Mapped[int] = mapped_column(default=1)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[UserAccount] = relationship(back_populates="rings")
    ring: Mapped[Ring] = relationship(back_populates="owner_links")


class UserAmuletOwnership(TimestampMixin, Base):
    """An amulet owned by an account, with account-specific progression."""

    __tablename__ = "user_amulet_ownership"
    __table_args__ = (UniqueConstraint("account_id", "amulet_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), index=True)
    amulet_id: Mapped[int] = mapped_column(ForeignKey("amulets.id"), index=True)

    level: Mapped[int] = mapped_column(default=1)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[UserAccount] = relationship(back_populates="amulets")
    amulet: Mapped[Amulet] = relationship(back_populates="owner_links")


class UserPetOwnership(TimestampMixin, Base):
    """A pet owned by an account, with account-specific progression."""

    __tablename__ = "user_pet_ownership"
    __table_args__ = (UniqueConstraint("account_id", "pet_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), index=True)

    level: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[UserAccount] = relationship(back_populates="pets")
    pet: Mapped[Pet] = relationship(back_populates="owner_links")


class UserRuneOwnership(TimestampMixin, Base):
    """A rune owned by an account, with account-specific progression."""

    __tablename__ = "user_rune_ownership"
    __table_args__ = (UniqueConstraint("account_id", "rune_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), index=True)
    rune_id: Mapped[int] = mapped_column(ForeignKey("runes.id"), index=True)

    level: Mapped[int] = mapped_column(default=1)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    socket_index: Mapped[int | None] = mapped_column(default=None)

    account: Mapped[UserAccount] = relationship(back_populates="runes")
    rune: Mapped[Rune] = relationship(back_populates="owner_links")


class UserSkillSelection(TimestampMixin, Base):
    """A skill unlocked/equipped by an account."""

    __tablename__ = "user_skill_selection"
    __table_args__ = (UniqueConstraint("account_id", "skill_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)

    is_unlocked: Mapped[bool] = mapped_column(Boolean, default=False)
    equipped_slot: Mapped[int | None] = mapped_column(default=None)

    account: Mapped[UserAccount] = relationship(back_populates="skill_selections")
    skill: Mapped[Skill] = relationship(back_populates="owner_links")


class UserChapterProgress(TimestampMixin, Base):
    """An account's clear progress on a given chapter."""

    __tablename__ = "user_chapter_progress"
    __table_args__ = (UniqueConstraint("account_id", "chapter_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), index=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), index=True)

    stars_earned: Mapped[int] = mapped_column(default=0)
    cleared: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(default=0)

    account: Mapped[UserAccount] = relationship(
        back_populates="chapter_progress", foreign_keys=[account_id]
    )
    chapter: Mapped[Chapter] = relationship(back_populates="progress_links")
