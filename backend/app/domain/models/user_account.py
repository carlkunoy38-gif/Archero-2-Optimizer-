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

Referential integrity
----------------------
Every ``account_id`` foreign key cascades at the database level
(``ondelete="CASCADE"``) so deleting an account removes its ownership
rows even via a bulk/raw-SQL delete that never touches the ORM.
Relationships on the ``UserAccount`` side additionally set
``passive_deletes=True``: this tells SQLAlchemy not to load and
individually delete each child row itself when the parent is deleted,
and instead let the database's ``ON DELETE CASCADE`` do it — the ORM
still handles ``delete-orphan`` semantics (removing a row from
``account.heroes`` without deleting the account). Foreign keys pointing
at *catalog* rows (``hero_id``, ``weapon_id``, ...) use
``ondelete="RESTRICT"``: a catalog item that is currently owned by some
account cannot be deleted out from under it. ``current_chapter_id`` uses
``ondelete="SET NULL"`` since "the chapter the player is currently on"
being removed from the catalog shouldn't take the account down with it.

These rules only take effect on SQLite because
``app.db.session.enable_sqlite_foreign_keys`` turns on
``PRAGMA foreign_keys``; PostgreSQL enforces them unconditionally.

Equipped-slot rules
--------------------
The following are deliberate Module 1 decisions (documented in
``docs/architecture.md``), enforced with partial unique indexes/unique
constraints rather than left to the API layer, so they hold even for a
buggy or malicious direct-DB write:

- At most one **active** hero per account (``UserHeroOwnership``).
- At most one **equipped** weapon per account (``UserWeaponOwnership``)
  — Archero 2 has a single weapon slot.
- At most one **active** pet per account (``UserPetOwnership``).
- At most one **equipped** ring and one **equipped** amulet per account
  (``UserRingOwnership`` / ``UserAmuletOwnership``) — placeholder
  single-slot assumption; revisit once real slot counts are confirmed.
- At most one **equipped** armor piece per (account, slot)
  (``UserArmorOwnership``), where ``slot`` is copied from the owned
  ``Armor`` row via a ``@validates`` hook so it can be indexed without a
  cross-table constraint.
- Rune sockets and skill-equip slots are unique per (account, slot
  index) among rows that actually occupy a slot — a plain
  ``UniqueConstraint`` works here because SQL treats ``NULL`` as
  distinct from every other ``NULL`` in a unique constraint, so
  "not socketed"/"not equipped" rows (``NULL`` index) never collide.

Maximum socket/slot *counts* (how many runes can be socketed, how many
skill slots exist) are still unknown pending real game data and are left
to be validated in the service layer in Module 2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base
from app.domain.models.enums import ArmorSlot
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
    __table_args__ = (
        CheckConstraint("gold >= 0", name="gold_non_negative"),
        CheckConstraint("gems >= 0", name="gems_non_negative"),
        CheckConstraint("energy >= 0", name="energy_non_negative"),
        CheckConstraint(
            "combat_power >= 0", name="combat_power_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    gold: Mapped[int] = mapped_column(default=0)
    gems: Mapped[int] = mapped_column(default=0)
    energy: Mapped[int] = mapped_column(default=0)
    combat_power: Mapped[float] = mapped_column(default=0.0)

    current_chapter_id: Mapped[int | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"), default=None
    )
    current_chapter: Mapped[Chapter | None] = relationship(
        back_populates="accounts_current_here", foreign_keys=[current_chapter_id]
    )

    heroes: Mapped[list[UserHeroOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan", passive_deletes=True
    )
    weapons: Mapped[list[UserWeaponOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan", passive_deletes=True
    )
    armor_pieces: Mapped[list[UserArmorOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan", passive_deletes=True
    )
    rings: Mapped[list[UserRingOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan", passive_deletes=True
    )
    amulets: Mapped[list[UserAmuletOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan", passive_deletes=True
    )
    pets: Mapped[list[UserPetOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan", passive_deletes=True
    )
    runes: Mapped[list[UserRuneOwnership]] = relationship(
        back_populates="account", cascade="all, delete-orphan", passive_deletes=True
    )
    skill_selections: Mapped[list[UserSkillSelection]] = relationship(
        back_populates="account", cascade="all, delete-orphan", passive_deletes=True
    )
    chapter_progress: Mapped[list[UserChapterProgress]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="UserChapterProgress.account_id",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"UserAccount(id={self.id!r}, display_name={self.display_name!r})"


class UserHeroOwnership(TimestampMixin, Base):
    """A hero owned by an account, with account-specific progression."""

    __tablename__ = "user_hero_ownership"
    __table_args__ = (
        UniqueConstraint("account_id", "hero_id"),
        CheckConstraint("level >= 1", name="level_min"),
        CheckConstraint("stars >= 0", name="stars_non_negative"),
        Index(
            "uq_user_hero_ownership_one_active_per_account",
            "account_id",
            unique=True,
            sqlite_where=text("is_active"),
            postgresql_where=text("is_active"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_accounts.id", ondelete="CASCADE"), index=True
    )
    hero_id: Mapped[int] = mapped_column(
        ForeignKey("heroes.id", ondelete="RESTRICT"), index=True
    )

    level: Mapped[int] = mapped_column(default=1)
    stars: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[UserAccount] = relationship(back_populates="heroes")
    hero: Mapped[Hero] = relationship(back_populates="owner_links")


class UserWeaponOwnership(TimestampMixin, Base):
    """A weapon owned by an account, with account-specific progression."""

    __tablename__ = "user_weapon_ownership"
    __table_args__ = (
        UniqueConstraint("account_id", "weapon_id"),
        CheckConstraint("level >= 1", name="level_min"),
        CheckConstraint(
            "star_level >= 0", name="star_level_non_negative"
        ),
        Index(
            "uq_user_weapon_ownership_one_equipped_per_account",
            "account_id",
            unique=True,
            sqlite_where=text("is_equipped"),
            postgresql_where=text("is_equipped"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_accounts.id", ondelete="CASCADE"), index=True
    )
    weapon_id: Mapped[int] = mapped_column(
        ForeignKey("weapons.id", ondelete="RESTRICT"), index=True
    )

    level: Mapped[int] = mapped_column(default=1)
    star_level: Mapped[int] = mapped_column(default=0)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[UserAccount] = relationship(back_populates="weapons")
    weapon: Mapped[Weapon] = relationship(back_populates="owner_links")


class UserArmorOwnership(TimestampMixin, Base):
    """An armor piece owned by an account, with account-specific progression.

    ``slot`` is a denormalized copy of ``armor.slot``, kept in sync by the
    ``_sync_slot`` validator whenever ``.armor`` is assigned. It exists
    purely so "at most one equipped item per slot" can be a single-table
    partial unique index instead of a cross-table constraint/trigger.
    """

    __tablename__ = "user_armor_ownership"
    __table_args__ = (
        UniqueConstraint("account_id", "armor_id"),
        CheckConstraint("level >= 1", name="level_min"),
        CheckConstraint(
            "star_level >= 0", name="star_level_non_negative"
        ),
        Index(
            "uq_user_armor_ownership_one_equipped_per_slot",
            "account_id",
            "slot",
            unique=True,
            sqlite_where=text("is_equipped"),
            postgresql_where=text("is_equipped"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_accounts.id", ondelete="CASCADE"), index=True
    )
    armor_id: Mapped[int] = mapped_column(
        ForeignKey("armor.id", ondelete="RESTRICT"), index=True
    )

    level: Mapped[int] = mapped_column(default=1)
    star_level: Mapped[int] = mapped_column(default=0)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    slot: Mapped[ArmorSlot] = mapped_column(Enum(ArmorSlot, name="armor_slot_ownership"))

    account: Mapped[UserAccount] = relationship(back_populates="armor_pieces")
    armor: Mapped[Armor] = relationship(back_populates="owner_links")

    @validates("armor")
    def _sync_slot(self, key: str, armor: Armor) -> Armor:
        self.slot = armor.slot
        return armor


class UserRingOwnership(TimestampMixin, Base):
    """A ring owned by an account, with account-specific progression."""

    __tablename__ = "user_ring_ownership"
    __table_args__ = (
        UniqueConstraint("account_id", "ring_id"),
        CheckConstraint("level >= 1", name="level_min"),
        Index(
            "uq_user_ring_ownership_one_equipped_per_account",
            "account_id",
            unique=True,
            sqlite_where=text("is_equipped"),
            postgresql_where=text("is_equipped"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_accounts.id", ondelete="CASCADE"), index=True
    )
    ring_id: Mapped[int] = mapped_column(
        ForeignKey("rings.id", ondelete="RESTRICT"), index=True
    )

    level: Mapped[int] = mapped_column(default=1)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[UserAccount] = relationship(back_populates="rings")
    ring: Mapped[Ring] = relationship(back_populates="owner_links")


class UserAmuletOwnership(TimestampMixin, Base):
    """An amulet owned by an account, with account-specific progression."""

    __tablename__ = "user_amulet_ownership"
    __table_args__ = (
        UniqueConstraint("account_id", "amulet_id"),
        CheckConstraint("level >= 1", name="level_min"),
        Index(
            "uq_user_amulet_ownership_one_equipped_per_account",
            "account_id",
            unique=True,
            sqlite_where=text("is_equipped"),
            postgresql_where=text("is_equipped"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_accounts.id", ondelete="CASCADE"), index=True
    )
    amulet_id: Mapped[int] = mapped_column(
        ForeignKey("amulets.id", ondelete="RESTRICT"), index=True
    )

    level: Mapped[int] = mapped_column(default=1)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[UserAccount] = relationship(back_populates="amulets")
    amulet: Mapped[Amulet] = relationship(back_populates="owner_links")


class UserPetOwnership(TimestampMixin, Base):
    """A pet owned by an account, with account-specific progression."""

    __tablename__ = "user_pet_ownership"
    __table_args__ = (
        UniqueConstraint("account_id", "pet_id"),
        CheckConstraint("level >= 1", name="level_min"),
        Index(
            "uq_user_pet_ownership_one_active_per_account",
            "account_id",
            unique=True,
            sqlite_where=text("is_active"),
            postgresql_where=text("is_active"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_accounts.id", ondelete="CASCADE"), index=True
    )
    pet_id: Mapped[int] = mapped_column(
        ForeignKey("pets.id", ondelete="RESTRICT"), index=True
    )

    level: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped[UserAccount] = relationship(back_populates="pets")
    pet: Mapped[Pet] = relationship(back_populates="owner_links")


class UserRuneOwnership(TimestampMixin, Base):
    """A rune owned by an account, with account-specific progression.

    ``socket_index`` doubles as the uniqueness key (two runes cannot
    occupy the same socket) and, via the check constraint below, as the
    single source of truth for whether the rune is socketed at all —
    ``is_equipped`` must agree with "is ``socket_index`` set".
    """

    __tablename__ = "user_rune_ownership"
    __table_args__ = (
        UniqueConstraint("account_id", "rune_id"),
        UniqueConstraint("account_id", "socket_index"),
        CheckConstraint("level >= 1", name="level_min"),
        CheckConstraint(
            "socket_index IS NULL OR socket_index >= 0",
            name="socket_index_non_negative",
        ),
        CheckConstraint(
            "(socket_index IS NULL AND NOT is_equipped) "
            "OR (socket_index IS NOT NULL AND is_equipped)",
            name="equipped_matches_socket",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_accounts.id", ondelete="CASCADE"), index=True
    )
    rune_id: Mapped[int] = mapped_column(
        ForeignKey("runes.id", ondelete="RESTRICT"), index=True
    )

    level: Mapped[int] = mapped_column(default=1)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    socket_index: Mapped[int | None] = mapped_column(default=None)

    account: Mapped[UserAccount] = relationship(back_populates="runes")
    rune: Mapped[Rune] = relationship(back_populates="owner_links")


class UserSkillSelection(TimestampMixin, Base):
    """A skill unlocked/equipped by an account.

    ``equipped_slot`` doubles as the uniqueness key (two skills cannot
    occupy the same slot) and the check constraint below ensures a skill
    cannot be equipped without first being unlocked.
    """

    __tablename__ = "user_skill_selection"
    __table_args__ = (
        UniqueConstraint("account_id", "skill_id"),
        UniqueConstraint("account_id", "equipped_slot"),
        CheckConstraint(
            "equipped_slot IS NULL OR equipped_slot >= 0",
            name="equipped_slot_non_negative",
        ),
        CheckConstraint(
            "equipped_slot IS NULL OR is_unlocked",
            name="equipped_requires_unlocked",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_accounts.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"), index=True
    )

    is_unlocked: Mapped[bool] = mapped_column(Boolean, default=False)
    equipped_slot: Mapped[int | None] = mapped_column(default=None)

    account: Mapped[UserAccount] = relationship(back_populates="skill_selections")
    skill: Mapped[Skill] = relationship(back_populates="owner_links")


class UserChapterProgress(TimestampMixin, Base):
    """An account's clear progress on a given chapter."""

    __tablename__ = "user_chapter_progress"
    __table_args__ = (
        UniqueConstraint("account_id", "chapter_id"),
        CheckConstraint(
            "stars_earned >= 0", name="stars_earned_non_negative"
        ),
        CheckConstraint(
            "attempts >= 0", name="attempts_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("user_accounts.id", ondelete="CASCADE"), index=True
    )
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id", ondelete="RESTRICT"), index=True
    )

    stars_earned: Mapped[int] = mapped_column(default=0)
    cleared: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(default=0)

    account: Mapped[UserAccount] = relationship(
        back_populates="chapter_progress", foreign_keys=[account_id]
    )
    chapter: Mapped[Chapter] = relationship(back_populates="progress_links")
