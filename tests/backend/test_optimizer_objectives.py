"""Unit tests for `app.optimizer.objectives.ObjectiveProfile`."""

from __future__ import annotations

import pytest

from app.core.exceptions import NotFoundError
from app.optimizer import objectives
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


def test_by_name_contains_every_public_profile() -> None:
    assert objectives.BY_NAME == {
        "balanced": objectives.BALANCED,
        "boss": objectives.BOSS,
        "farm": objectives.FARM,
        "survival": objectives.SURVIVAL,
    }


def test_boss_weighs_offense_relative_to_aoe_more_than_farm_does() -> None:
    context = _context(attack=1000.0, projectile_count=3.0)

    boss_score = objectives.BOSS.evaluate(context)
    farm_score = objectives.FARM.evaluate(context)

    # Same build, different objective weighting of the same underlying
    # offense_score/aoe_score numbers — the two objectives must not
    # collapse to the same evaluation.
    assert boss_score != farm_score


def test_survival_rewards_defense_more_than_boss_does() -> None:
    tanky = _context(max_hp=2000.0, defense=100.0)

    boss_score = objectives.BOSS.evaluate(tanky)
    survival_score = objectives.SURVIVAL.evaluate(tanky)

    assert survival_score > boss_score


def test_evaluate_boosts_mobility_weight_when_underpowered() -> None:
    on_pace = _context(
        movement_speed=1.0, combat_power=1000.0, recommended_combat_power=1000.0
    )
    underpowered = _context(
        movement_speed=1.0, combat_power=100.0, recommended_combat_power=1000.0
    )

    assert objectives.BALANCED.evaluate(underpowered) > objectives.BALANCED.evaluate(on_pace)


def test_farm_weighs_summon_investment_more_than_boss_does() -> None:
    summon_build = _context(circle_damage=30.0, plant_damage=15.0)

    boss_score = objectives.BOSS.evaluate(summon_build)
    farm_score = objectives.FARM.evaluate(summon_build)

    # Same summon investment, different objective weighting — farming
    # should value it more than a boss fight does (see
    # weights.OBJECTIVE_WEIGHTS's "summon" column).
    assert farm_score > boss_score


def test_evaluate_rewards_summon_investment_over_an_identical_build_without_it() -> None:
    no_summons = _context(attack=100.0)
    with_summons = _context(attack=100.0, fire_damage=20.0, poison_damage=20.0)

    assert objectives.FARM.evaluate(with_summons) > objectives.FARM.evaluate(no_summons)


def test_resolve_returns_the_matching_profile() -> None:
    assert objectives.resolve("farm") is objectives.FARM


def test_resolve_raises_not_found_for_an_unknown_name() -> None:
    with pytest.raises(NotFoundError):
        objectives.resolve("nonsense")
