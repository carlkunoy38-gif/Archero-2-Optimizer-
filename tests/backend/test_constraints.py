"""Database-integrity tests: foreign keys, CHECK constraints, and the
equipped/slot uniqueness rules described in ``docs/architecture.md``.

These deliberately go around the ORM's own bookkeeping where possible
(raw ``insert``/``delete`` core statements) to prove the *database*
enforces these rules, not just well-behaved application code.
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.models import (
    Amulet,
    Armor,
    ArmorSlot,
    Chapter,
    Hero,
    HeroClass,
    Pet,
    Rarity,
    Ring,
    Rune,
    RuneType,
    Skill,
    SkillType,
    StatType,
    UserAccount,
    UserAmuletOwnership,
    UserArmorOwnership,
    UserChapterProgress,
    UserHeroOwnership,
    UserPetOwnership,
    UserRingOwnership,
    UserRuneOwnership,
    UserSkillSelection,
    UserWeaponOwnership,
    Weapon,
)


@pytest.fixture()
def hero(db: Session) -> Hero:
    h = Hero(name="Hero", hero_class=HeroClass.WARRIOR, rarity=Rarity.EPIC)
    db.add(h)
    db.commit()
    return h


@pytest.fixture()
def second_hero(db: Session) -> Hero:
    h = Hero(name="Second Hero", hero_class=HeroClass.MAGE, rarity=Rarity.RARE)
    db.add(h)
    db.commit()
    return h


@pytest.fixture()
def weapon(db: Session) -> Weapon:
    w = Weapon(name="Weapon", weapon_type="bow", rarity=Rarity.RARE)
    db.add(w)
    db.commit()
    return w


@pytest.fixture()
def second_weapon(db: Session) -> Weapon:
    w = Weapon(name="Second Weapon", weapon_type="staff", rarity=Rarity.EPIC)
    db.add(w)
    db.commit()
    return w


@pytest.fixture()
def chapter(db: Session) -> Chapter:
    c = Chapter(number=1, name="Chapter One")
    db.add(c)
    db.commit()
    return c


@pytest.fixture()
def account(db: Session) -> UserAccount:
    a = UserAccount(display_name="carl")
    db.add(a)
    db.commit()
    return a


class TestForeignKeyIntegrity:
    def test_ownership_rejects_nonexistent_account(self, db: Session, hero: Hero) -> None:
        with pytest.raises(IntegrityError):
            db.execute(
                insert(UserHeroOwnership).values(account_id=999_999, hero_id=hero.id, level=1)
            )
            db.commit()

    def test_ownership_rejects_nonexistent_catalog_item(
        self, db: Session, account: UserAccount
    ) -> None:
        with pytest.raises(IntegrityError):
            db.execute(
                insert(UserHeroOwnership).values(
                    account_id=account.id, hero_id=999_999, level=1
                )
            )
            db.commit()

    def test_deleting_owned_catalog_item_is_restricted(
        self, db: Session, account: UserAccount, hero: Hero
    ) -> None:
        db.add(UserHeroOwnership(account=account, hero=hero))
        db.commit()

        with pytest.raises(IntegrityError):
            db.execute(delete(Hero).where(Hero.id == hero.id))
            db.commit()

    def test_deleting_unowned_catalog_item_succeeds(self, db: Session, hero: Hero) -> None:
        db.execute(delete(Hero).where(Hero.id == hero.id))
        db.commit()
        assert db.scalar(select(func.count()).select_from(Hero)) == 0

    def test_deleting_current_chapter_sets_account_column_null(
        self, db: Session, chapter: Chapter
    ) -> None:
        account = UserAccount(display_name="carl", current_chapter=chapter)
        db.add(account)
        db.commit()
        account_id = account.id

        db.execute(delete(Chapter).where(Chapter.id == chapter.id))
        db.commit()

        db.expire_all()
        refreshed = db.get(UserAccount, account_id)
        assert refreshed is not None
        assert refreshed.current_chapter_id is None

    def test_deleting_account_via_core_delete_cascades_ownership_rows(
        self, db: Session, hero: Hero, weapon: Weapon
    ) -> None:
        """Bulk/raw-SQL deletes never touch the ORM's Python-side cascade
        logic, so this proves the ``ON DELETE CASCADE`` is a real
        database-level rule and not just ORM bookkeeping."""

        account = UserAccount(display_name="carl")
        db.add(account)
        db.flush()
        db.add(UserHeroOwnership(account=account, hero=hero))
        db.add(UserWeaponOwnership(account=account, weapon=weapon))
        db.commit()
        account_id = account.id

        db.execute(delete(UserAccount).where(UserAccount.id == account_id))
        db.commit()

        assert db.scalar(select(func.count()).select_from(UserHeroOwnership)) == 0
        assert db.scalar(select(func.count()).select_from(UserWeaponOwnership)) == 0
        assert db.scalar(select(func.count()).select_from(Hero)) == 1
        assert db.scalar(select(func.count()).select_from(Weapon)) == 1


class TestCheckConstraints:
    @pytest.mark.parametrize("field", ["gold", "gems", "energy", "combat_power"])
    def test_account_resource_fields_reject_negative(self, db: Session, field: str) -> None:
        with pytest.raises(IntegrityError):
            db.add(UserAccount(display_name="carl", **{field: -1}))
            db.commit()

    def test_hero_ownership_rejects_level_below_one(
        self, db: Session, account: UserAccount, hero: Hero
    ) -> None:
        with pytest.raises(IntegrityError):
            db.add(UserHeroOwnership(account=account, hero=hero, level=0))
            db.commit()

    def test_hero_ownership_rejects_negative_stars(
        self, db: Session, account: UserAccount, hero: Hero
    ) -> None:
        with pytest.raises(IntegrityError):
            db.add(UserHeroOwnership(account=account, hero=hero, stars=-1))
            db.commit()

    def test_weapon_ownership_rejects_negative_star_level(
        self, db: Session, account: UserAccount, weapon: Weapon
    ) -> None:
        with pytest.raises(IntegrityError):
            db.add(UserWeaponOwnership(account=account, weapon=weapon, star_level=-1))
            db.commit()

    def test_chapter_progress_rejects_negative_attempts(
        self, db: Session, account: UserAccount, chapter: Chapter
    ) -> None:
        with pytest.raises(IntegrityError):
            db.add(UserChapterProgress(account=account, chapter=chapter, attempts=-1))
            db.commit()

    def test_chapter_progress_rejects_negative_stars_earned(
        self, db: Session, account: UserAccount, chapter: Chapter
    ) -> None:
        with pytest.raises(IntegrityError):
            db.add(UserChapterProgress(account=account, chapter=chapter, stars_earned=-1))
            db.commit()

    def test_rune_ownership_rejects_negative_socket_index(
        self, db: Session, account: UserAccount
    ) -> None:
        rune = Rune(name="Rune", rune_type=RuneType.OFFENSE, rarity=Rarity.RARE)
        db.add(rune)
        db.flush()
        with pytest.raises(IntegrityError):
            db.add(
                UserRuneOwnership(
                    account=account, rune=rune, is_equipped=True, socket_index=-1
                )
            )
            db.commit()

    def test_skill_selection_rejects_equipped_without_unlocked(
        self, db: Session, account: UserAccount
    ) -> None:
        skill = Skill(name="Skill", skill_type=SkillType.OFFENSIVE)
        db.add(skill)
        db.flush()
        with pytest.raises(IntegrityError):
            db.add(
                UserSkillSelection(
                    account=account, skill=skill, is_unlocked=False, equipped_slot=0
                )
            )
            db.commit()


class TestEquippedSlotRules:
    def test_only_one_active_hero_per_account(
        self, db: Session, account: UserAccount, hero: Hero, second_hero: Hero
    ) -> None:
        db.add(UserHeroOwnership(account=account, hero=hero, is_active=True))
        db.commit()

        db.add(UserHeroOwnership(account=account, hero=second_hero, is_active=True))
        with pytest.raises(IntegrityError):
            db.commit()

    def test_only_one_equipped_weapon_per_account(
        self, db: Session, account: UserAccount, weapon: Weapon, second_weapon: Weapon
    ) -> None:
        db.add(UserWeaponOwnership(account=account, weapon=weapon, is_equipped=True))
        db.commit()

        db.add(
            UserWeaponOwnership(account=account, weapon=second_weapon, is_equipped=True)
        )
        with pytest.raises(IntegrityError):
            db.commit()

    def test_only_one_active_pet_per_account(self, db: Session, account: UserAccount) -> None:
        pet_a = Pet(name="Pet A", rarity=Rarity.RARE, bonus_stat=StatType.HEALTH)
        pet_b = Pet(name="Pet B", rarity=Rarity.EPIC, bonus_stat=StatType.ATTACK)
        db.add_all([pet_a, pet_b])
        db.flush()

        db.add(UserPetOwnership(account=account, pet=pet_a, is_active=True))
        db.commit()

        db.add(UserPetOwnership(account=account, pet=pet_b, is_active=True))
        with pytest.raises(IntegrityError):
            db.commit()

    def test_only_one_equipped_ring_per_account(self, db: Session, account: UserAccount) -> None:
        ring_a = Ring(name="Ring A", rarity=Rarity.RARE, primary_stat=StatType.ATTACK)
        ring_b = Ring(name="Ring B", rarity=Rarity.EPIC, primary_stat=StatType.DEFENSE)
        db.add_all([ring_a, ring_b])
        db.flush()

        db.add(UserRingOwnership(account=account, ring=ring_a, is_equipped=True))
        db.commit()

        db.add(UserRingOwnership(account=account, ring=ring_b, is_equipped=True))
        with pytest.raises(IntegrityError):
            db.commit()

    def test_only_one_equipped_amulet_per_account(
        self, db: Session, account: UserAccount
    ) -> None:
        amulet_a = Amulet(name="Amulet A", rarity=Rarity.RARE, primary_stat=StatType.ATTACK)
        amulet_b = Amulet(name="Amulet B", rarity=Rarity.EPIC, primary_stat=StatType.DEFENSE)
        db.add_all([amulet_a, amulet_b])
        db.flush()

        db.add(UserAmuletOwnership(account=account, amulet=amulet_a, is_equipped=True))
        db.commit()

        db.add(UserAmuletOwnership(account=account, amulet=amulet_b, is_equipped=True))
        with pytest.raises(IntegrityError):
            db.commit()

    def test_armor_slot_is_synced_from_catalog_item(
        self, db: Session, account: UserAccount
    ) -> None:
        helmet = Armor(name="Helmet", slot=ArmorSlot.HELMET, rarity=Rarity.COMMON)
        db.add(helmet)
        db.flush()

        ownership = UserArmorOwnership(armor=helmet, account=account, is_equipped=True)
        assert ownership.slot is ArmorSlot.HELMET

    def test_only_one_equipped_armor_per_slot(self, db: Session, account: UserAccount) -> None:
        helmet_a = Armor(name="Helmet A", slot=ArmorSlot.HELMET, rarity=Rarity.COMMON)
        helmet_b = Armor(name="Helmet B", slot=ArmorSlot.HELMET, rarity=Rarity.RARE)
        db.add_all([helmet_a, helmet_b])
        db.flush()

        db.add(UserArmorOwnership(armor=helmet_a, account=account, is_equipped=True))
        db.commit()

        db.add(UserArmorOwnership(armor=helmet_b, account=account, is_equipped=True))
        with pytest.raises(IntegrityError):
            db.commit()

    def test_different_armor_slots_can_both_be_equipped(
        self, db: Session, account: UserAccount
    ) -> None:
        helmet = Armor(name="Helmet", slot=ArmorSlot.HELMET, rarity=Rarity.COMMON)
        boots = Armor(name="Boots", slot=ArmorSlot.BOOTS, rarity=Rarity.COMMON)
        db.add_all([helmet, boots])
        db.flush()

        db.add(UserArmorOwnership(armor=helmet, account=account, is_equipped=True))
        db.add(UserArmorOwnership(armor=boots, account=account, is_equipped=True))
        db.commit()  # should not raise

        assert db.scalar(select(func.count()).select_from(UserArmorOwnership)) == 2

    def test_rune_socket_index_is_unique_per_account(
        self, db: Session, account: UserAccount
    ) -> None:
        rune_a = Rune(name="Rune A", rune_type=RuneType.OFFENSE, rarity=Rarity.RARE)
        rune_b = Rune(name="Rune B", rune_type=RuneType.DEFENSE, rarity=Rarity.EPIC)
        db.add_all([rune_a, rune_b])
        db.flush()

        db.add(
            UserRuneOwnership(account=account, rune=rune_a, is_equipped=True, socket_index=0)
        )
        db.commit()

        db.add(
            UserRuneOwnership(account=account, rune=rune_b, is_equipped=True, socket_index=0)
        )
        with pytest.raises(IntegrityError):
            db.commit()

    def test_multiple_unsocketed_runes_are_allowed(
        self, db: Session, account: UserAccount
    ) -> None:
        rune_a = Rune(name="Rune A", rune_type=RuneType.OFFENSE, rarity=Rarity.RARE)
        rune_b = Rune(name="Rune B", rune_type=RuneType.DEFENSE, rarity=Rarity.EPIC)
        db.add_all([rune_a, rune_b])
        db.flush()

        db.add(UserRuneOwnership(account=account, rune=rune_a, is_equipped=False))
        db.add(UserRuneOwnership(account=account, rune=rune_b, is_equipped=False))
        db.commit()  # should not raise: both socket_index are NULL

        assert db.scalar(select(func.count()).select_from(UserRuneOwnership)) == 2

    def test_skill_equipped_slot_is_unique_per_account(
        self, db: Session, account: UserAccount
    ) -> None:
        skill_a = Skill(name="Skill A", skill_type=SkillType.OFFENSIVE)
        skill_b = Skill(name="Skill B", skill_type=SkillType.DEFENSIVE)
        db.add_all([skill_a, skill_b])
        db.flush()

        db.add(
            UserSkillSelection(
                account=account, skill=skill_a, is_unlocked=True, equipped_slot=0
            )
        )
        db.commit()

        db.add(
            UserSkillSelection(
                account=account, skill=skill_b, is_unlocked=True, equipped_slot=0
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
