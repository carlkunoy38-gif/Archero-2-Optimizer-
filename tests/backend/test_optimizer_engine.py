"""Unit tests for `app.optimizer.engine`'s scoring primitives.

Every primitive is a pure function of a `BuildContext`, so these are
plain dataclass-in, float-out tests — no database involved.
"""

from __future__ import annotations

from app.optimizer import engine
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


def test_offense_score_scales_with_attack() -> None:
    weak = engine.offense_score(_context(attack=100.0))
    strong = engine.offense_score(_context(attack=200.0))
    assert strong == 2 * weak


def test_offense_score_scales_with_attack_speed() -> None:
    baseline = engine.offense_score(_context(attack=100.0, attack_speed=0.0))
    faster = engine.offense_score(_context(attack=100.0, attack_speed=1.0))
    assert faster == 2 * baseline


def test_offense_score_scales_with_crit() -> None:
    no_crit = engine.offense_score(_context(attack=100.0))
    with_crit = engine.offense_score(_context(attack=100.0, crit_chance=0.5, crit_damage=2.0))
    assert with_crit == 100.0 * 2.0
    assert with_crit > no_crit


def test_defense_score_scales_with_max_hp() -> None:
    weak = engine.defense_score(_context(max_hp=100.0))
    strong = engine.defense_score(_context(max_hp=200.0))
    assert strong == 2 * weak


def test_defense_score_scales_with_defense_and_dodge() -> None:
    baseline = engine.defense_score(_context(max_hp=100.0))
    with_defense = engine.defense_score(_context(max_hp=100.0, defense=100.0))
    with_dodge = engine.defense_score(_context(max_hp=100.0, dodge=1.0))
    assert with_defense == 2 * baseline
    assert with_dodge == 2 * baseline


def test_mobility_score_combines_movement_speed_and_dodge() -> None:
    assert engine.mobility_score(_context(movement_speed=1.5, dodge=0.25)) == 1.75


def test_utility_score_is_resource_gain() -> None:
    assert engine.utility_score(_context(resource_gain=42.0)) == 42.0


def test_aoe_score_is_zero_with_no_extra_projectiles_or_bounces() -> None:
    # projectile_count defaults to 1.0 (the baseline single projectile) —
    # that alone should contribute nothing to aoe_score.
    assert engine.aoe_score(_context(attack=500.0)) == 0.0


def test_aoe_score_scales_with_extra_projectiles_but_with_diminishing_returns() -> None:
    zero_extra = engine.aoe_score(_context(attack=100.0, projectile_count=1.0))
    one_extra = engine.aoe_score(_context(attack=100.0, projectile_count=2.0))
    two_extra = engine.aoe_score(_context(attack=100.0, projectile_count=3.0))

    first_gain = one_extra - zero_extra
    second_gain = two_extra - one_extra

    assert first_gain > 0.0
    # Diminishing returns: the second extra projectile is worth less
    # than the first — this is what lets an account's *already
    # selected* projectile skills change how much a new one is worth.
    assert 0.0 < second_gain < first_gain


def test_aoe_score_scales_with_bounce_count() -> None:
    assert engine.aoe_score(_context(attack=100.0, bounce_count=2.0)) > 0.0


def test_aoe_score_weighs_projectiles_and_bounces_differently() -> None:
    # Equal-magnitude projectile vs. bounce bonuses should not produce
    # the same aoe_score — otherwise a PROJECTILE_COUNT skill and a
    # BOUNCE_COUNT skill of the same tier would still tie.
    from_projectile = engine.aoe_score(_context(attack=100.0, projectile_count=2.0))
    from_bounce = engine.aoe_score(_context(attack=100.0, bounce_count=1.0))
    assert from_projectile != from_bounce
    assert from_projectile > 0.0
    assert from_bounce > 0.0
