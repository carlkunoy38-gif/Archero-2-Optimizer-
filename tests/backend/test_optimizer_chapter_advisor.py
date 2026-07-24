"""Tests for `app.optimizer.chapter_scoring` and
`app.optimizer.advisors.chapter_advisor`.

The property that matters most: "best chapter to farm" and "best
chapter to clear next" are genuinely different questions that can (and
should) have different answers for the same build — farming rewards a
comfortable, cheap chapter; progression rewards the furthest one still
safely reachable. When the account is under-powered for the top
progression pick, the advisor should say so and point at the Upgrade
Advisor's own top recommendation rather than leaving the player stuck.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.models import Chapter, Hero, HeroClass, Rarity, UserAccount, UserHeroOwnership
from app.optimizer import chapter_scoring, objectives, weights
from app.optimizer.advisors import chapter_advisor
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


def _chapter(
    chapter_id: int, number: int, recommended_combat_power: float, energy_cost: int = 5
) -> Chapter:
    chapter = Chapter(
        id=chapter_id,
        number=number,
        name=f"Chapter {number}",
        recommended_combat_power=recommended_combat_power,
        energy_cost=energy_cost,
    )
    return chapter


# --- chapter_scoring primitives -----------------------------------------


def test_power_gap_for_chapter_defaults_to_neutral_when_unset() -> None:
    context = _context(combat_power=500.0)
    chapter = _chapter(1, 1, recommended_combat_power=0.0)

    assert chapter_scoring.power_gap_for_chapter(context, chapter) == 1.0


def test_clear_safety_is_zero_at_or_below_the_minimum_gap() -> None:
    assert chapter_scoring.clear_safety(weights.MIN_SAFE_POWER_GAP_RATIO) == 0.0
    assert chapter_scoring.clear_safety(0.1) == 0.0


def test_clear_safety_is_one_at_or_above_full_power() -> None:
    assert chapter_scoring.clear_safety(1.0) == 1.0
    assert chapter_scoring.clear_safety(5.0) == 1.0


def test_clear_safety_ramps_linearly_between_the_thresholds() -> None:
    midpoint = (weights.MIN_SAFE_POWER_GAP_RATIO + 1.0) / 2
    assert chapter_scoring.clear_safety(midpoint) == pytest.approx(0.5)


def test_farm_suitability_penalizes_higher_energy_cost() -> None:
    context = _context(combat_power=1000.0, resource_gain=10.0)
    cheap = _chapter(1, 1, recommended_combat_power=500.0, energy_cost=5)
    expensive = _chapter(2, 2, recommended_combat_power=500.0, energy_cost=20)

    cheap_score = chapter_scoring.farm_suitability(context, cheap, objectives.FARM)
    expensive_score = chapter_scoring.farm_suitability(context, expensive, objectives.FARM)

    assert cheap_score > expensive_score


def test_progression_suitability_rewards_further_chapters_when_both_safe() -> None:
    context = _context(combat_power=1000.0)
    near = _chapter(1, 1, recommended_combat_power=500.0)
    far = _chapter(2, 2, recommended_combat_power=900.0)

    assert chapter_scoring.progression_suitability(
        context, far, objectives.BALANCED
    ) > chapter_scoring.progression_suitability(context, near, objectives.BALANCED)


def test_progression_suitability_is_zero_when_unsafe_regardless_of_distance() -> None:
    context = _context(combat_power=100.0)
    unreachable = _chapter(1, 1, recommended_combat_power=10_000.0)

    assert chapter_scoring.progression_suitability(context, unreachable, objectives.BALANCED) == 0.0


# --- Pure score_chapter/advise -------------------------------------------


def test_farm_and_progression_modes_can_recommend_different_chapters() -> None:
    context = _context(combat_power=1000.0, resource_gain=10.0)
    cheap_and_safe = _chapter(1, 1, recommended_combat_power=400.0, energy_cost=3)
    far_and_safe = _chapter(2, 2, recommended_combat_power=950.0, energy_cost=30)

    farm_result = chapter_advisor.advise(
        context, [cheap_and_safe, far_and_safe], objectives.FARM
    )
    progression_result = chapter_advisor.advise(
        context, [cheap_and_safe, far_and_safe], objectives.BALANCED
    )

    assert farm_result.recommended.option.id == cheap_and_safe.id
    assert progression_result.recommended.option.id == far_and_safe.id


def test_advise_requires_at_least_one_candidate() -> None:
    with pytest.raises(ValueError):
        chapter_advisor.advise(_context(), [])


def test_advise_breaks_ties_deterministically_by_catalog_id() -> None:
    context = _context(combat_power=1000.0)
    twin_a = _chapter(5, 1, recommended_combat_power=500.0)
    twin_b = _chapter(2, 2, recommended_combat_power=500.0)

    forward = chapter_advisor.advise(context, [twin_a, twin_b])
    backward = chapter_advisor.advise(context, [twin_b, twin_a])

    assert forward.recommended.option.id == backward.recommended.option.id == 2


def test_unsafe_chapter_summary_says_so() -> None:
    context = _context(combat_power=10.0)
    unreachable = _chapter(1, 1, recommended_combat_power=10_000.0)

    scored = chapter_advisor.score_chapter(context, unreachable, objectives.BALANCED)

    assert "too far above your current power" in scored.summary


# --- DB-aware advise_for_account -----------------------------------------


def test_advise_for_account_farm_mode_prefers_cheap_safe_chapter(
    db: Session, account: UserAccount
) -> None:
    account.combat_power = 1000.0
    cheap = Chapter(number=1, name="Easy Meadow", recommended_combat_power=400.0, energy_cost=3)
    costly = Chapter(number=2, name="Hard Peak", recommended_combat_power=900.0, energy_cost=30)
    db.add_all([cheap, costly])
    db.commit()

    result = chapter_advisor.advise_for_account(db, account.id, objective_name="farm")

    assert result.recommended.option.id == cheap.id


def test_advise_for_account_progression_mode_prefers_furthest_safe_chapter(
    db: Session, account: UserAccount
) -> None:
    account.combat_power = 1000.0
    near = Chapter(number=1, name="Easy Meadow", recommended_combat_power=400.0, energy_cost=3)
    far = Chapter(number=2, name="Far Ridge", recommended_combat_power=950.0, energy_cost=10)
    db.add_all([near, far])
    db.commit()

    result = chapter_advisor.advise_for_account(db, account.id, objective_name="balanced")

    assert result.recommended.option.id == far.id


def test_advise_for_account_suggests_an_upgrade_when_top_pick_is_unsafe(
    db: Session, account: UserAccount
) -> None:
    account.combat_power = 50
    account.gold = 5000
    hero = Hero(
        name="Hero",
        hero_class=HeroClass.WARRIOR,
        rarity=Rarity.EPIC,
        base_attack=100.0,
        base_defense=20.0,
        base_hp=500.0,
        base_attack_speed=1.0,
    )
    db.add(hero)
    db.commit()
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero.id, level=5, is_active=True))
    chapter = Chapter(number=1, name="Dragon Peak", recommended_combat_power=900.0, energy_cost=15)
    db.add(chapter)
    db.commit()

    result = chapter_advisor.advise_for_account(db, account.id, objective_name="balanced")

    top = result.recommended
    assert "consider this first" in top.summary.lower()
    assert any("upgrade first" in reason.lower() for reason in top.reasons)


def test_advise_for_account_does_not_suggest_upgrade_in_farm_mode(
    db: Session, account: UserAccount
) -> None:
    # Farm mode never scores above 0 for an unsafe chapter either, but
    # it shouldn't trigger the progression-only "upgrade first" cross-call.
    account.combat_power = 10
    account.gold = 5000
    chapter = Chapter(number=1, name="Dragon Peak", recommended_combat_power=900.0, energy_cost=15)
    db.add(chapter)
    db.commit()

    result = chapter_advisor.advise_for_account(db, account.id, objective_name="farm")

    assert "upgrade first" not in result.recommended.summary.lower()


def test_advise_for_account_raises_not_found_for_missing_account(db: Session) -> None:
    with pytest.raises(NotFoundError):
        chapter_advisor.advise_for_account(db, 999999)


def test_advise_for_account_raises_not_found_for_unknown_objective(
    db: Session, account: UserAccount, chapter: Chapter
) -> None:
    with pytest.raises(NotFoundError):
        chapter_advisor.advise_for_account(db, account.id, objective_name="nonsense")


def test_advise_for_account_raises_not_found_for_empty_catalog(
    db: Session, account: UserAccount
) -> None:
    with pytest.raises(NotFoundError):
        chapter_advisor.advise_for_account(db, account.id)
