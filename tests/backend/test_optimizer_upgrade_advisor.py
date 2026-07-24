"""Tests for `app.optimizer.advisors.upgrade_advisor`.

The properties that matter most: an upgrade the account can't afford is
never even scored, and an upgrade that wouldn't actually improve the
build is filtered out of the final ranking even if it's affordable —
"if an upgrade isn't optimal, don't recommend it."
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.models import (
    Hero,
    HeroClass,
    Rarity,
    UserAccount,
    UserHeroOwnership,
    UserWeaponOwnership,
    Weapon,
)
from app.optimizer import weights
from app.optimizer.advisors import upgrade_advisor
from app.optimizer.advisors.upgrade_advisor import UpgradeCategory, UpgradeOption
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


# --- max_affordable_levels ---------------------------------------------


def test_max_affordable_levels_returns_zero_when_even_one_level_is_unaffordable() -> None:
    # BASE_UPGRADE_COST_PER_LEVEL == 50.0, so level 1 -> 2 costs 50 * 1 == 50.
    levels, cost = upgrade_advisor.max_affordable_levels(current_level=1, gold=49.0)
    assert levels == 0
    assert cost == 0.0


def test_max_affordable_levels_buys_as_many_as_it_can_afford() -> None:
    # level1->2 costs 50*1=50, level2->3 costs 50*2=100; total for two
    # levels is 150, affordable with 150 gold but not a third (150 more).
    levels, cost = upgrade_advisor.max_affordable_levels(current_level=1, gold=150.0)
    assert levels == 2
    assert cost == 150.0


def test_max_affordable_levels_is_capped_even_with_unlimited_gold() -> None:
    levels, _cost = upgrade_advisor.max_affordable_levels(current_level=1, gold=10**9)
    assert levels == weights.MAX_UPGRADE_LEVELS_CONSIDERED


# --- Pure score_upgrade/advise ------------------------------------------


def _option(
    catalog_id: int, name: str, from_level: int, to_level: int, cost: float
) -> UpgradeOption:
    return UpgradeOption(
        category=UpgradeCategory.WEAPON,
        ownership_id=catalog_id,
        catalog_id=catalog_id,
        name=name,
        from_level=from_level,
        to_level=to_level,
        gold_cost=cost,
    )


def test_score_upgrade_reports_expected_percentage_build_improvement() -> None:
    # `context` already reflects the item at its *current* level (the
    # same way `build_context` bakes in whatever's currently equipped),
    # so `current_contribution` is what gets subtracted back out before
    # `upgraded_contribution` is added — not an extra addition on top.
    context = _context(attack=100.0)
    option = _option(1, "Weapon", 1, 2, cost=50.0)

    scored = upgrade_advisor.score_upgrade(
        context,
        option,
        current_contribution={"attack": 20.0},
        upgraded_contribution={"attack": 40.0},
    )

    # offense_score before = 100 (attack directly, no speed/crit);
    # offense_score after = 100 - 20 + 40 = 120; balanced offense_weight
    # = 0.02, so before_score = 2.0, after_score = 2.4, gain = 0.4,
    # gain_pct = 0.4 / 2.0 * 100 = 20%.
    assert scored.score == pytest.approx(20.0)
    assert "expected build improvement" in scored.summary.lower()


def test_advise_ranks_the_best_expected_improvement_first() -> None:
    context = _context(attack=100.0)
    small = (
        _option(1, "Small", 1, 2, cost=50.0),
        {"attack": 10.0},
        {"attack": 12.0},
    )
    big = (
        _option(2, "Big", 1, 2, cost=50.0),
        {"attack": 10.0},
        {"attack": 60.0},
    )

    result = upgrade_advisor.advise(context, [small, big])

    assert result.recommended.option.name == "Big"


def test_advise_requires_at_least_one_candidate() -> None:
    with pytest.raises(ValueError):
        upgrade_advisor.advise(_context(), [])


def test_advise_breaks_ties_deterministically_by_catalog_id() -> None:
    context = _context(attack=100.0)
    twin_a = (_option(5, "Twin A", 1, 2, 50.0), {"attack": 0.0}, {"attack": 10.0})
    twin_b = (_option(2, "Twin B", 1, 2, 50.0), {"attack": 0.0}, {"attack": 10.0})

    forward = upgrade_advisor.advise(context, [twin_a, twin_b])
    backward = upgrade_advisor.advise(context, [twin_b, twin_a])

    assert forward.recommended.option.catalog_id == backward.recommended.option.catalog_id == 2


# --- DB-aware advise_for_account -----------------------------------------


def test_advise_for_account_recommends_the_best_affordable_upgrade(
    db: Session, account: UserAccount
) -> None:
    account.gold = 1000
    hero = Hero(
        name="Hero",
        hero_class=HeroClass.WARRIOR,
        rarity=Rarity.EPIC,
        base_attack=100.0,
        base_defense=10.0,
        base_hp=200.0,
        base_attack_speed=0.0,
    )
    weapon = Weapon(
        name="Weapon", weapon_type="bow", rarity=Rarity.RARE, base_damage=5.0, base_attack_speed=0.0
    )
    db.add_all([hero, weapon])
    db.commit()
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero.id, level=3, is_active=True))
    db.add(
        UserWeaponOwnership(account_id=account.id, weapon_id=weapon.id, level=3, is_equipped=True)
    )
    db.commit()

    result = upgrade_advisor.advise_for_account(db, account.id)

    # The hero (base_attack 100) improves the build far more per level
    # than the weapon (base_damage 5) at the same cost curve.
    assert result.recommended.option.category is UpgradeCategory.HERO


def test_advise_for_account_never_recommends_an_unaffordable_upgrade(
    db: Session, account: UserAccount, hero: Hero
) -> None:
    account.gold = 0
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero.id, level=1, is_active=True))
    db.commit()

    with pytest.raises(NotFoundError):
        upgrade_advisor.advise_for_account(db, account.id)


def test_advise_for_account_raises_not_found_for_missing_account(db: Session) -> None:
    with pytest.raises(NotFoundError):
        upgrade_advisor.advise_for_account(db, 999999)


def test_advise_for_account_raises_not_found_for_unknown_objective(
    db: Session, account: UserAccount, hero: Hero
) -> None:
    account.gold = 1000
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero.id, level=1, is_active=True))
    db.commit()

    with pytest.raises(NotFoundError):
        upgrade_advisor.advise_for_account(db, account.id, objective_name="nonsense")
