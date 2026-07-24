"""Unit tests for `app.optimizer.context.build_context`.

`build_context` takes an already eager-loaded `UserAccount` (as returned
by `app.repositories.account_repository.get_account_with_detail`) and
aggregates it into a `BuildContext`. These tests build real ownership
rows through the ORM directly (not through the service/API layer, which
is already covered by Module 2's own tests) and assert the aggregation
math against the same formulas `context.py` uses.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.models import (
    Amulet,
    Armor,
    Chapter,
    EffectType,
    Hero,
    Pet,
    Ring,
    Rune,
    RuneType,
    Skill,
    SkillEffect,
    SkillType,
    StatType,
    UserAccount,
    UserAmuletOwnership,
    UserArmorOwnership,
    UserHeroOwnership,
    UserPetOwnership,
    UserRingOwnership,
    UserRuneOwnership,
    UserSkillSelection,
    UserWeaponOwnership,
    Weapon,
)
from app.optimizer.context import build_context
from app.repositories.account_repository import get_account_with_detail


def _load(db: Session, account_id: int) -> UserAccount:
    account = get_account_with_detail(db, account_id)
    assert account is not None
    return account


def test_build_context_on_empty_account_is_all_zero(db: Session, account: UserAccount) -> None:
    context = build_context(_load(db, account.id))

    assert context.account_id == account.id
    assert context.hero_level == 0
    assert context.attack == 0.0
    assert context.defense == 0.0
    assert context.max_hp == 0.0
    assert context.attack_speed == 0.0
    assert context.crit_chance == 0.0
    assert context.movement_speed == 0.0
    assert context.dodge == 0.0
    assert context.resource_gain == 0.0
    assert context.recommended_combat_power is None
    assert context.power_gap_ratio == 1.0
    assert context.projectile_count == 1.0
    assert context.bounce_count == 0.0
    assert context.selected_skill_ids == frozenset()


def test_build_context_uses_active_hero_scaled_by_level(
    db: Session, account: UserAccount, hero: Hero
) -> None:
    hero.base_attack = 100.0
    hero.base_defense = 20.0
    hero.base_hp = 300.0
    hero.base_attack_speed = 0.0
    db.add(
        UserHeroOwnership(account_id=account.id, hero_id=hero.id, level=6, is_active=True)
    )
    db.commit()

    context = build_context(_load(db, account.id))

    # _level_multiplier(6) == 1 + 5 * 0.08 == 1.4
    assert context.hero_level == 6
    assert context.attack == 100.0 * 1.4
    assert context.defense == 20.0 * 1.4
    assert context.max_hp == 300.0 * 1.4


def test_build_context_ignores_inactive_hero(db: Session, account: UserAccount, hero: Hero) -> None:
    hero.base_attack = 999.0
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero.id, level=1, is_active=False))
    db.commit()

    context = build_context(_load(db, account.id))

    assert context.hero_level == 0
    assert context.attack == 0.0


def test_build_context_uses_equipped_weapon_scaled_by_level_and_star(
    db: Session, account: UserAccount, weapon: Weapon
) -> None:
    weapon.base_damage = 50.0
    weapon.base_attack_speed = 0.0
    weapon.crit_chance_bonus = 0.1
    db.add(
        UserWeaponOwnership(
            account_id=account.id,
            weapon_id=weapon.id,
            level=1,
            star_level=2,
            is_equipped=True,
        )
    )
    db.commit()

    context = build_context(_load(db, account.id))

    # level_multiplier(1) == 1.0, star_multiplier(2) == 1 + 2 * 0.05 == 1.1
    assert context.attack == 50.0 * 1.0 * 1.1
    assert context.crit_chance == 0.1


def test_build_context_ignores_unequipped_weapon(
    db: Session, account: UserAccount, weapon: Weapon
) -> None:
    weapon.base_damage = 999.0
    db.add(UserWeaponOwnership(account_id=account.id, weapon_id=weapon.id, is_equipped=False))
    db.commit()

    context = build_context(_load(db, account.id))

    assert context.attack == 0.0


def test_build_context_sums_equipped_armor_pieces(
    db: Session, account: UserAccount, armor_item: Armor
) -> None:
    armor_item.base_defense = 10.0
    armor_item.base_hp = 40.0
    db.add(
        UserArmorOwnership(
            account_id=account.id,
            armor_id=armor_item.id,
            armor=armor_item,
            level=1,
            star_level=0,
            is_equipped=True,
        )
    )
    db.commit()

    context = build_context(_load(db, account.id))

    assert context.defense == 10.0
    assert context.max_hp == 40.0


def test_build_context_maps_ring_and_amulet_primary_stat(
    db: Session, account: UserAccount, ring: Ring, amulet: Amulet
) -> None:
    ring.primary_stat = StatType.CRIT_CHANCE
    ring.primary_stat_value = 0.2
    amulet.primary_stat = StatType.CRIT_DAMAGE
    amulet.primary_stat_value = 1.5

    db.add(UserRingOwnership(account_id=account.id, ring_id=ring.id, level=1, is_equipped=True))
    db.add(
        UserAmuletOwnership(
            account_id=account.id, amulet_id=amulet.id, level=1, is_equipped=True
        )
    )
    db.commit()

    context = build_context(_load(db, account.id))

    assert context.crit_chance == 0.2
    assert context.crit_damage == 1.5


def test_build_context_uses_active_pet_bonus_stat(
    db: Session, account: UserAccount, pet: Pet
) -> None:
    pet.bonus_stat = StatType.DODGE
    pet.bonus_stat_value = 0.15
    db.add(UserPetOwnership(account_id=account.id, pet_id=pet.id, level=1, is_active=True))
    db.commit()

    context = build_context(_load(db, account.id))

    assert context.dodge == 0.15


def test_build_context_maps_rune_type_to_stat_field(
    db: Session, account: UserAccount, rune: Rune
) -> None:
    rune.rune_type = RuneType.UTILITY
    rune.effect_value = 5.0
    db.add(
        UserRuneOwnership(
            account_id=account.id,
            rune_id=rune.id,
            level=1,
            is_equipped=True,
            socket_index=0,
        )
    )
    db.commit()

    context = build_context(_load(db, account.id))

    assert context.resource_gain == 5.0


def test_power_gap_ratio_uses_current_chapter(
    db: Session, account: UserAccount, chapter: Chapter
) -> None:
    chapter.recommended_combat_power = 1000.0
    account.combat_power = 250.0
    account.current_chapter = chapter
    db.commit()

    context = build_context(_load(db, account.id))

    assert context.recommended_combat_power == 1000.0
    assert context.power_gap_ratio == 0.25


def test_power_gap_ratio_defaults_to_neutral_without_current_chapter(
    db: Session, account: UserAccount
) -> None:
    account.combat_power = 250.0
    db.commit()

    context = build_context(_load(db, account.id))

    assert context.recommended_combat_power is None
    assert context.power_gap_ratio == 1.0


def test_build_context_folds_equipped_skill_effects_into_totals(
    db: Session, account: UserAccount
) -> None:
    multishot = Skill(name="Multishot", skill_type=SkillType.OFFENSIVE, tier=3)
    multishot.effects = [SkillEffect(effect_type=EffectType.PROJECTILE_COUNT, value=1.0)]
    db.add(multishot)
    db.commit()
    db.add(
        UserSkillSelection(
            account_id=account.id, skill_id=multishot.id, is_unlocked=True, equipped_slot=0
        )
    )
    db.commit()

    context = build_context(_load(db, account.id))

    assert context.projectile_count == 2.0
    assert context.selected_skill_ids == frozenset({multishot.id})


def test_build_context_sums_effects_across_multiple_equipped_skills(
    db: Session, account: UserAccount
) -> None:
    first = Skill(name="Multishot", skill_type=SkillType.OFFENSIVE, tier=3)
    first.effects = [SkillEffect(effect_type=EffectType.PROJECTILE_COUNT, value=1.0)]
    second = Skill(name="Front Arrow", skill_type=SkillType.OFFENSIVE, tier=2)
    second.effects = [SkillEffect(effect_type=EffectType.PROJECTILE_COUNT, value=1.0)]
    db.add_all([first, second])
    db.commit()
    db.add(
        UserSkillSelection(
            account_id=account.id, skill_id=first.id, is_unlocked=True, equipped_slot=0
        )
    )
    db.add(
        UserSkillSelection(
            account_id=account.id, skill_id=second.id, is_unlocked=True, equipped_slot=1
        )
    )
    db.commit()

    context = build_context(_load(db, account.id))

    assert context.projectile_count == 3.0
    assert context.selected_skill_ids == frozenset({first.id, second.id})


def test_build_context_ignores_unlocked_but_unequipped_skill(
    db: Session, account: UserAccount
) -> None:
    multishot = Skill(name="Multishot", skill_type=SkillType.OFFENSIVE, tier=3)
    multishot.effects = [SkillEffect(effect_type=EffectType.PROJECTILE_COUNT, value=1.0)]
    db.add(multishot)
    db.commit()
    db.add(
        UserSkillSelection(
            account_id=account.id, skill_id=multishot.id, is_unlocked=True, equipped_slot=None
        )
    )
    db.commit()

    context = build_context(_load(db, account.id))

    assert context.projectile_count == 1.0
    assert context.selected_skill_ids == frozenset()
