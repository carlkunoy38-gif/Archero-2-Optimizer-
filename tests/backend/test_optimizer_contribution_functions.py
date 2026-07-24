"""Unit tests for `app.optimizer.context`'s per-item contribution
functions — the pure "catalog row at a level/star -> BuildContext field
deltas" math that `build_context` uses for currently-equipped items and
that the Gear/Upgrade Advisors reuse for candidates that aren't
currently equipped or aren't at their current level. No database
needed: these take plain in-memory ORM objects, never a session.
"""

from __future__ import annotations

import pytest

from app.domain.models import (
    Armor,
    ArmorSlot,
    EffectType,
    Hero,
    HeroClass,
    Rarity,
    RuneType,
    Skill,
    SkillEffect,
    SkillType,
    StatType,
    Weapon,
)
from app.optimizer import weights
from app.optimizer.context import (
    armor_contribution,
    hero_contribution,
    rune_contribution,
    skill_effect_contribution,
    stat_item_contribution,
    weapon_contribution,
)


def test_hero_contribution_scales_attack_defense_hp_by_level() -> None:
    hero = Hero(
        name="Hero",
        hero_class=HeroClass.WARRIOR,
        rarity=Rarity.EPIC,
        base_attack=100.0,
        base_defense=20.0,
        base_hp=300.0,
        base_attack_speed=0.5,
    )

    contribution = hero_contribution(hero, level=6)

    # _level_multiplier(6) == 1 + 5 * 0.08 == 1.4
    assert contribution["attack"] == 140.0
    assert contribution["defense"] == 28.0
    assert contribution["max_hp"] == 420.0
    # attack_speed is not level-scaled
    assert contribution["attack_speed"] == 0.5


def test_weapon_contribution_scales_by_level_and_star() -> None:
    weapon = Weapon(
        name="Weapon",
        weapon_type="bow",
        rarity=Rarity.RARE,
        base_damage=50.0,
        base_attack_speed=0.2,
        crit_chance_bonus=0.1,
    )

    contribution = weapon_contribution(weapon, level=1, star_level=2)

    # level_multiplier(1) == 1.0, star_multiplier(2) == 1 + 2 * 0.05 == 1.1
    assert contribution["attack"] == pytest.approx(55.0)
    assert contribution["attack_speed"] == 0.2
    assert contribution["crit_chance"] == 0.1


def test_armor_contribution_scales_defense_and_hp() -> None:
    armor = Armor(
        name="Helmet", slot=ArmorSlot.HELMET, rarity=Rarity.COMMON, base_defense=10.0, base_hp=40.0
    )

    contribution = armor_contribution(armor, level=1, star_level=0)

    assert contribution == {"defense": 10.0, "max_hp": 40.0}


def test_stat_item_contribution_maps_known_stat_type() -> None:
    contribution = stat_item_contribution(StatType.CRIT_CHANCE, 0.2, level=1)
    assert contribution == {"crit_chance": 0.2}


def test_stat_item_contribution_scales_by_level() -> None:
    contribution = stat_item_contribution(StatType.ATTACK, 100.0, level=6)
    # _level_multiplier(6) == 1.4
    assert contribution == {"attack": 140.0}


def test_rune_contribution_maps_rune_type_to_field() -> None:
    contribution = rune_contribution(RuneType.UTILITY, 5.0, level=1)
    assert contribution == {"resource_gain": 5.0}


def test_skill_effect_contribution_sums_multiple_effects_on_same_field() -> None:
    skill = Skill(name="Multishot", skill_type=SkillType.OFFENSIVE, tier=3)
    skill.effects = [
        SkillEffect(effect_type=EffectType.PROJECTILE_COUNT, value=1.0),
        SkillEffect(effect_type=EffectType.PROJECTILE_COUNT, value=0.5),
    ]

    contribution = skill_effect_contribution(skill)

    assert contribution == {"projectile_count": 1.5}


def test_skill_effect_contribution_is_empty_for_a_skill_with_no_effects() -> None:
    skill = Skill(name="Mystery", skill_type=SkillType.UTILITY, tier=1)
    skill.effects = []

    assert skill_effect_contribution(skill) == {}


def test_every_rune_type_is_mapped_to_a_build_context_field() -> None:
    # Documents the "silently ignore an unmapped type, don't raise"
    # contract rune_contribution relies on: it's only safe because
    # every current RuneType has an entry today.
    assert set(RuneType) == set(weights.RUNE_TYPE_STAT_FIELD)
