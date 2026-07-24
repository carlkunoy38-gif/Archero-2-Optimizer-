"""Unit tests for the Phase 1 domain models.

Covers: each catalog entity can be created, UserAccount ownership
relationships resolve in both directions, uniqueness constraints on
ownership tables are enforced, and deleting a UserAccount cascades to
its ownership rows without touching the shared catalog rows.
"""

from __future__ import annotations

import pytest
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
    UserHeroOwnership,
    UserWeaponOwnership,
    Weapon,
)


@pytest.fixture()
def sample_hero(db: Session) -> Hero:
    hero = Hero(
        name="Sample Hero",
        hero_class=HeroClass.WARRIOR,
        rarity=Rarity.EPIC,
        base_hp=1000.0,
        base_attack=50.0,
        base_defense=20.0,
    )
    db.add(hero)
    db.commit()
    return hero


@pytest.fixture()
def sample_weapon(db: Session) -> Weapon:
    weapon = Weapon(
        name="Sample Bow",
        weapon_type="bow",
        rarity=Rarity.RARE,
        base_damage=25.0,
    )
    db.add(weapon)
    db.commit()
    return weapon


@pytest.fixture()
def sample_chapter(db: Session) -> Chapter:
    chapter = Chapter(number=1, name="Whispering Forest", recommended_combat_power=1000.0)
    db.add(chapter)
    db.commit()
    return chapter


class TestCatalogModels:
    def test_hero_roundtrip(self, db: Session, sample_hero: Hero) -> None:
        fetched = db.query(Hero).filter_by(name="Sample Hero").one()
        assert fetched.hero_class is HeroClass.WARRIOR
        assert fetched.rarity is Rarity.EPIC
        assert fetched.base_hp == 1000.0

    def test_weapon_roundtrip(self, db: Session, sample_weapon: Weapon) -> None:
        fetched = db.query(Weapon).filter_by(name="Sample Bow").one()
        assert fetched.weapon_type == "bow"
        assert fetched.rarity is Rarity.RARE

    def test_armor_roundtrip(self, db: Session) -> None:
        armor = Armor(
            name="Sample Helmet", slot=ArmorSlot.HELMET, rarity=Rarity.COMMON, base_defense=5.0
        )
        db.add(armor)
        db.commit()
        fetched = db.query(Armor).filter_by(name="Sample Helmet").one()
        assert fetched.slot is ArmorSlot.HELMET

    def test_ring_roundtrip(self, db: Session) -> None:
        ring = Ring(
            name="Sample Ring",
            rarity=Rarity.RARE,
            primary_stat=StatType.CRIT_CHANCE,
            primary_stat_value=5.0,
        )
        db.add(ring)
        db.commit()
        fetched = db.query(Ring).filter_by(name="Sample Ring").one()
        assert fetched.primary_stat is StatType.CRIT_CHANCE

    def test_amulet_roundtrip(self, db: Session) -> None:
        amulet = Amulet(
            name="Sample Amulet",
            rarity=Rarity.EPIC,
            primary_stat=StatType.ATTACK,
            primary_stat_value=10.0,
        )
        db.add(amulet)
        db.commit()
        fetched = db.query(Amulet).filter_by(name="Sample Amulet").one()
        assert fetched.primary_stat is StatType.ATTACK

    def test_pet_roundtrip(self, db: Session) -> None:
        pet = Pet(
            name="Sample Pet",
            rarity=Rarity.RARE,
            bonus_stat=StatType.HEALTH,
            bonus_stat_value=100.0,
        )
        db.add(pet)
        db.commit()
        fetched = db.query(Pet).filter_by(name="Sample Pet").one()
        assert fetched.bonus_stat is StatType.HEALTH

    def test_rune_roundtrip(self, db: Session) -> None:
        rune = Rune(name="Sample Rune", rune_type=RuneType.OFFENSE, rarity=Rarity.EPIC)
        db.add(rune)
        db.commit()
        fetched = db.query(Rune).filter_by(name="Sample Rune").one()
        assert fetched.rune_type is RuneType.OFFENSE

    def test_skill_roundtrip(self, db: Session) -> None:
        skill = Skill(name="Sample Skill", skill_type=SkillType.OFFENSIVE, tier=2)
        db.add(skill)
        db.commit()
        fetched = db.query(Skill).filter_by(name="Sample Skill").one()
        assert fetched.skill_type is SkillType.OFFENSIVE
        assert fetched.tier == 2

    def test_chapter_roundtrip(self, db: Session, sample_chapter: Chapter) -> None:
        fetched = db.query(Chapter).filter_by(number=1).one()
        assert fetched.name == "Whispering Forest"


class TestUserAccountRelationships:
    def test_account_owns_hero_with_progression(
        self, db: Session, sample_hero: Hero
    ) -> None:
        account = UserAccount(display_name="carl")
        db.add(account)
        db.flush()

        ownership = UserHeroOwnership(account=account, hero=sample_hero, level=10, stars=3)
        db.add(ownership)
        db.commit()

        fetched = db.query(UserAccount).filter_by(display_name="carl").one()
        assert len(fetched.heroes) == 1
        assert fetched.heroes[0].level == 10
        assert fetched.heroes[0].hero.name == "Sample Hero"
        # Inverse direction: the catalog hero can see who owns it.
        assert sample_hero.owner_links[0].account.display_name == "carl"

    def test_account_current_chapter(self, db: Session, sample_chapter: Chapter) -> None:
        account = UserAccount(display_name="carl", current_chapter=sample_chapter)
        db.add(account)
        db.commit()

        fetched = db.query(UserAccount).filter_by(display_name="carl").one()
        assert fetched.current_chapter is not None
        assert fetched.current_chapter.name == "Whispering Forest"
        assert fetched in sample_chapter.accounts_current_here

    def test_duplicate_hero_ownership_is_rejected(
        self, db: Session, sample_hero: Hero
    ) -> None:
        account = UserAccount(display_name="carl")
        db.add(account)
        db.flush()

        db.add(UserHeroOwnership(account=account, hero=sample_hero, level=1))
        db.commit()

        db.add(UserHeroOwnership(account=account, hero=sample_hero, level=2))
        with pytest.raises(IntegrityError):
            db.commit()

    def test_deleting_account_cascades_ownership_but_not_catalog(
        self, db: Session, sample_hero: Hero, sample_weapon: Weapon
    ) -> None:
        account = UserAccount(display_name="carl")
        db.add(account)
        db.flush()

        db.add(UserHeroOwnership(account=account, hero=sample_hero, level=5))
        db.add(UserWeaponOwnership(account=account, weapon=sample_weapon, level=3))
        db.commit()

        db.delete(account)
        db.commit()

        assert db.query(UserHeroOwnership).count() == 0
        assert db.query(UserWeaponOwnership).count() == 0
        # Catalog rows are untouched by deleting the account that owned them.
        assert db.query(Hero).filter_by(name="Sample Hero").one_or_none() is not None
        assert db.query(Weapon).filter_by(name="Sample Bow").one_or_none() is not None

    def test_display_name_is_unique(self, db: Session) -> None:
        db.add(UserAccount(display_name="carl"))
        db.commit()

        db.add(UserAccount(display_name="carl"))
        with pytest.raises(IntegrityError):
            db.commit()
