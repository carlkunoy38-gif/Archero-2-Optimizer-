"""Unit tests for `app.optimizer.simulator.apply_skill`.

Pure function, no database — a `Skill` with its `effects` relationship
already populated in memory is enough.
"""

from __future__ import annotations

import pytest

from app.domain.models import EffectType, Skill, SkillEffect, SkillType
from app.optimizer import simulator
from app.optimizer.context import BuildContext


def _context(**overrides: float | int | None) -> BuildContext:
    defaults: dict[str, float | int | None] = {
        "account_id": 1,
        "hero_level": 1,
        "attack": 0.0,
        "defense": 0.0,
        "max_hp": 0.0,
        "attack_speed": 0.0,
        "crit_chance": 0.0,
        "crit_damage": 0.0,
        "movement_speed": 0.0,
        "life_steal": 0.0,
        "dodge": 0.0,
        "resource_gain": 0.0,
        "combat_power": 0.0,
        "recommended_combat_power": None,
    }
    defaults.update(overrides)
    return BuildContext(**defaults)  # type: ignore[arg-type]


def _skill(*effects: SkillEffect, tier: int = 1) -> Skill:
    skill = Skill(name="Test Skill", skill_type=SkillType.OFFENSIVE, tier=tier)
    skill.effects = list(effects)
    return skill


def test_apply_skill_adds_effect_value_onto_matching_field() -> None:
    skill = _skill(SkillEffect(effect_type=EffectType.PROJECTILE_COUNT, value=1.0))
    context = _context()

    result = simulator.apply_skill(context, skill)

    assert result.projectile_count == context.projectile_count + 1.0


def test_apply_skill_sums_multiple_effects_on_the_same_field() -> None:
    skill = _skill(
        SkillEffect(effect_type=EffectType.DEFENSE_BONUS, value=10.0),
        SkillEffect(effect_type=EffectType.DEFENSE_BONUS, value=5.0),
    )
    context = _context(defense=20.0)

    result = simulator.apply_skill(context, skill)

    assert result.defense == 35.0


def test_apply_skill_with_no_effects_returns_equivalent_context() -> None:
    skill = _skill()
    context = _context(attack=123.0)

    result = simulator.apply_skill(context, skill)

    assert result == context


def test_apply_skill_does_not_mutate_the_original_context() -> None:
    skill = _skill(SkillEffect(effect_type=EffectType.MAX_HP_BONUS, value=100.0))
    context = _context(max_hp=200.0)

    simulator.apply_skill(context, skill)

    assert context.max_hp == 200.0


def test_apply_skill_only_touches_fields_its_effects_target() -> None:
    skill = _skill(SkillEffect(effect_type=EffectType.ATTACK_SPEED_MULTIPLIER, value=0.2))
    context = _context(attack=50.0, defense=30.0, attack_speed=0.1)

    result = simulator.apply_skill(context, skill)

    assert result.attack_speed == pytest.approx(0.3)
    assert result.attack == 50.0
    assert result.defense == 30.0


# --- replace_contribution: the generic gear-swap/level-up primitive --------


def test_replace_contribution_with_empty_before_is_a_pure_addition() -> None:
    context = _context(attack=100.0)

    result = simulator.replace_contribution(context, before={}, after={"attack": 50.0})

    assert result.attack == 150.0


def test_replace_contribution_with_empty_after_is_a_pure_removal() -> None:
    context = _context(attack=100.0)

    result = simulator.replace_contribution(context, before={"attack": 40.0}, after={})

    assert result.attack == 60.0


def test_replace_contribution_swaps_one_items_stats_for_anothers() -> None:
    # e.g. unequipping a weapon contributing {attack: 80, crit_chance: 0.1}
    # in favor of one contributing {attack: 60, attack_speed: 0.3}.
    context = _context(attack=200.0, crit_chance=0.2, attack_speed=0.5)

    result = simulator.replace_contribution(
        context,
        before={"attack": 80.0, "crit_chance": 0.1},
        after={"attack": 60.0, "attack_speed": 0.3},
    )

    assert result.attack == 180.0  # 200 - 80 + 60
    assert result.crit_chance == pytest.approx(0.1)  # 0.2 - 0.1 (removed, nothing added)
    assert result.attack_speed == pytest.approx(0.8)  # 0.5 + 0.3 (added, nothing removed)


def test_replace_contribution_with_identical_before_and_after_is_a_no_op() -> None:
    context = _context(attack=100.0, defense=50.0)
    same = {"attack": 30.0, "defense": 10.0}

    result = simulator.replace_contribution(context, before=same, after=dict(same))

    assert result == context


def test_replace_contribution_does_not_mutate_the_original_context() -> None:
    context = _context(attack=100.0)

    simulator.replace_contribution(context, before={}, after={"attack": 999.0})

    assert context.attack == 100.0


def test_apply_skill_delegates_to_replace_contribution_with_empty_before() -> None:
    # apply_skill is documented as a pure addition via replace_contribution
    # — verify the two give identical results for the same effect.
    skill = _skill(SkillEffect(effect_type=EffectType.PROJECTILE_COUNT, value=2.0))
    context = _context(attack=10.0)

    via_apply_skill = simulator.apply_skill(context, skill)
    via_replace_contribution = simulator.replace_contribution(
        context, before={}, after={"projectile_count": 2.0}
    )

    assert via_apply_skill == via_replace_contribution
