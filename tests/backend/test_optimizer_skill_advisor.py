"""Tests for `app.optimizer.advisors.skill_advisor`.

The test that matters most here is
`test_same_candidates_rank_differently_for_different_builds`: it proves
the whole point of Module 3 — the same three skill choices, offered to
two accounts with different real, DB-backed builds, produce a different
*recommended* skill, not merely different scores. There is no static
tier list anywhere in this module; the ranking is entirely a function of
each account's aggregated `BuildContext`.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.models import (
    Hero,
    HeroClass,
    Rarity,
    Skill,
    SkillType,
    UserAccount,
    UserHeroOwnership,
)
from app.optimizer.advisors import skill_advisor
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


@pytest.fixture()
def offensive_skill(db: Session) -> Skill:
    instance = Skill(name="Multishot", skill_type=SkillType.OFFENSIVE, tier=3)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def defensive_skill(db: Session) -> Skill:
    instance = Skill(name="Iron Skin", skill_type=SkillType.DEFENSIVE, tier=3)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def movement_skill(db: Session) -> Skill:
    instance = Skill(name="Dash", skill_type=SkillType.MOVEMENT, tier=3)
    db.add(instance)
    db.commit()
    return instance


# --- Pure `score_skill`/`advise` -------------------------------------------


def test_offensive_skill_scores_higher_with_more_offense(offensive_skill: Skill) -> None:
    weak = skill_advisor.score_skill(_context(attack=10.0), offensive_skill)
    strong = skill_advisor.score_skill(_context(attack=1000.0), offensive_skill)
    assert strong.score > weak.score


def test_defensive_skill_scores_higher_the_more_deficient_the_build(
    defensive_skill: Skill,
) -> None:
    tanky = skill_advisor.score_skill(_context(max_hp=1000.0), defensive_skill)
    squishy = skill_advisor.score_skill(_context(max_hp=10.0), defensive_skill)
    assert squishy.score > tanky.score


def test_movement_skill_scores_higher_when_underpowered(movement_skill: Skill) -> None:
    underpowered = skill_advisor.score_skill(
        _context(combat_power=100.0, recommended_combat_power=1000.0), movement_skill
    )
    on_pace = skill_advisor.score_skill(
        _context(combat_power=1000.0, recommended_combat_power=1000.0), movement_skill
    )
    assert underpowered.score > on_pace.score


def test_advise_ranks_best_option_first(
    offensive_skill: Skill, defensive_skill: Skill, movement_skill: Skill
) -> None:
    result = skill_advisor.advise(
        _context(attack=5000.0, attack_speed=1.0),
        [offensive_skill, defensive_skill, movement_skill],
    )
    assert result.recommended.option is offensive_skill
    assert [scored.score for scored in result.ranked] == sorted(
        (scored.score for scored in result.ranked), reverse=True
    )


def test_advise_requires_at_least_one_candidate() -> None:
    with pytest.raises(ValueError):
        skill_advisor.advise(_context(), [])


def test_same_candidates_rank_differently_for_different_builds(
    offensive_skill: Skill, defensive_skill: Skill, movement_skill: Skill
) -> None:
    """The core Module 3 requirement: no static tier list. The exact
    same three candidate skills must be able to produce a different
    *recommended* skill depending on the build they're scored against."""

    glass_cannon = _context(attack=2000.0, attack_speed=1.0, defense=100.0, max_hp=600.0)
    underdog = _context(attack=200.0, defense=0.0, max_hp=50.0)

    candidates = [offensive_skill, defensive_skill, movement_skill]
    cannon_result = skill_advisor.advise(glass_cannon, candidates)
    underdog_result = skill_advisor.advise(underdog, candidates)

    assert cannon_result.recommended.option is offensive_skill
    assert underdog_result.recommended.option is defensive_skill
    assert cannon_result.recommended.option is not underdog_result.recommended.option


# --- DB-aware `advise_for_account` -----------------------------------------


@pytest.fixture()
def strong_account(db: Session) -> UserAccount:
    account = UserAccount(display_name="strong")
    hero_row = Hero(
        name="Strong Hero",
        hero_class=HeroClass.WARRIOR,
        rarity=Rarity.EPIC,
        base_attack=2000.0,
        base_defense=100.0,
        base_hp=600.0,
        base_attack_speed=1.0,
    )
    db.add_all([account, hero_row])
    db.commit()
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero_row.id, level=1, is_active=True))
    db.commit()
    return account


@pytest.fixture()
def weak_account(db: Session) -> UserAccount:
    account = UserAccount(display_name="weak")
    hero_row = Hero(
        name="Weak Hero",
        hero_class=HeroClass.WARRIOR,
        rarity=Rarity.COMMON,
        base_attack=200.0,
        base_defense=0.0,
        base_hp=50.0,
        base_attack_speed=0.0,
    )
    db.add_all([account, hero_row])
    db.commit()
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero_row.id, level=1, is_active=True))
    db.commit()
    return account


def test_advise_for_account_reflects_real_db_backed_builds(
    db: Session,
    strong_account: UserAccount,
    weak_account: UserAccount,
    offensive_skill: Skill,
    defensive_skill: Skill,
    movement_skill: Skill,
) -> None:
    candidate_ids = [offensive_skill.id, defensive_skill.id, movement_skill.id]

    strong_result = skill_advisor.advise_for_account(db, strong_account.id, candidate_ids)
    weak_result = skill_advisor.advise_for_account(db, weak_account.id, candidate_ids)

    assert strong_result.recommended.option.id == offensive_skill.id
    assert weak_result.recommended.option.id == defensive_skill.id


def test_advise_for_account_raises_not_found_for_missing_account(
    db: Session, offensive_skill: Skill
) -> None:
    with pytest.raises(NotFoundError):
        skill_advisor.advise_for_account(db, 999999, [offensive_skill.id])


def test_advise_for_account_raises_not_found_for_missing_skill(
    db: Session, weak_account: UserAccount
) -> None:
    with pytest.raises(NotFoundError):
        skill_advisor.advise_for_account(db, weak_account.id, [999999])


def test_advise_for_account_deduplicates_candidate_ids(
    db: Session, weak_account: UserAccount, offensive_skill: Skill, defensive_skill: Skill
) -> None:
    result = skill_advisor.advise_for_account(
        db, weak_account.id, [offensive_skill.id, offensive_skill.id, defensive_skill.id]
    )
    assert len(result.ranked) == 2
