"""Read-only business logic for the nine catalog resources.

There isn't much "business logic" here beyond "fetch it, and turn a
missing row into a `NotFoundError`" — which is exactly why this stays a
thin pass-through to `app/repositories/` rather than something routes
call directly: keeping the 404-on-missing decision in one layer means
every catalog route looks the same, and a future rule (e.g. hiding
unreleased items) has one place to go.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
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
    Weapon,
)
from app.repositories import (
    amulet_repository,
    armor_repository,
    chapter_repository,
    hero_repository,
    pet_repository,
    ring_repository,
    rune_repository,
    skill_repository,
    weapon_repository,
)


def list_heroes(
    db: Session, *, limit: int, offset: int, rarity: Rarity | None, hero_class: HeroClass | None
) -> list[Hero]:
    return hero_repository.list_heroes(
        db, limit=limit, offset=offset, rarity=rarity, hero_class=hero_class
    )


def get_hero(db: Session, hero_id: int) -> Hero:
    hero = hero_repository.get_hero(db, hero_id)
    if hero is None:
        raise NotFoundError(f"Hero {hero_id} not found")
    return hero


def list_weapons(
    db: Session, *, limit: int, offset: int, rarity: Rarity | None, weapon_type: str | None
) -> list[Weapon]:
    return weapon_repository.list_weapons(
        db, limit=limit, offset=offset, rarity=rarity, weapon_type=weapon_type
    )


def get_weapon(db: Session, weapon_id: int) -> Weapon:
    weapon = weapon_repository.get_weapon(db, weapon_id)
    if weapon is None:
        raise NotFoundError(f"Weapon {weapon_id} not found")
    return weapon


def list_armor(
    db: Session, *, limit: int, offset: int, rarity: Rarity | None, slot: ArmorSlot | None
) -> list[Armor]:
    return armor_repository.list_armor(db, limit=limit, offset=offset, rarity=rarity, slot=slot)


def get_armor(db: Session, armor_id: int) -> Armor:
    armor = armor_repository.get_armor(db, armor_id)
    if armor is None:
        raise NotFoundError(f"Armor {armor_id} not found")
    return armor


def list_rings(db: Session, *, limit: int, offset: int, rarity: Rarity | None) -> list[Ring]:
    return ring_repository.list_rings(db, limit=limit, offset=offset, rarity=rarity)


def get_ring(db: Session, ring_id: int) -> Ring:
    ring = ring_repository.get_ring(db, ring_id)
    if ring is None:
        raise NotFoundError(f"Ring {ring_id} not found")
    return ring


def list_amulets(db: Session, *, limit: int, offset: int, rarity: Rarity | None) -> list[Amulet]:
    return amulet_repository.list_amulets(db, limit=limit, offset=offset, rarity=rarity)


def get_amulet(db: Session, amulet_id: int) -> Amulet:
    amulet = amulet_repository.get_amulet(db, amulet_id)
    if amulet is None:
        raise NotFoundError(f"Amulet {amulet_id} not found")
    return amulet


def list_pets(db: Session, *, limit: int, offset: int, rarity: Rarity | None) -> list[Pet]:
    return pet_repository.list_pets(db, limit=limit, offset=offset, rarity=rarity)


def get_pet(db: Session, pet_id: int) -> Pet:
    pet = pet_repository.get_pet(db, pet_id)
    if pet is None:
        raise NotFoundError(f"Pet {pet_id} not found")
    return pet


def list_runes(
    db: Session, *, limit: int, offset: int, rarity: Rarity | None, rune_type: RuneType | None
) -> list[Rune]:
    return rune_repository.list_runes(
        db, limit=limit, offset=offset, rarity=rarity, rune_type=rune_type
    )


def get_rune(db: Session, rune_id: int) -> Rune:
    rune = rune_repository.get_rune(db, rune_id)
    if rune is None:
        raise NotFoundError(f"Rune {rune_id} not found")
    return rune


def list_skills(
    db: Session, *, limit: int, offset: int, skill_type: SkillType | None
) -> list[Skill]:
    return skill_repository.list_skills(db, limit=limit, offset=offset, skill_type=skill_type)


def get_skill(db: Session, skill_id: int) -> Skill:
    skill = skill_repository.get_skill(db, skill_id)
    if skill is None:
        raise NotFoundError(f"Skill {skill_id} not found")
    return skill


def list_chapters(db: Session, *, limit: int, offset: int) -> list[Chapter]:
    return chapter_repository.list_chapters(db, limit=limit, offset=offset)


def get_chapter(db: Session, chapter_id: int) -> Chapter:
    chapter = chapter_repository.get_chapter(db, chapter_id)
    if chapter is None:
        raise NotFoundError(f"Chapter {chapter_id} not found")
    return chapter
