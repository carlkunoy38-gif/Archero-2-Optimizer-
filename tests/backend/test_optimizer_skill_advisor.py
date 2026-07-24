"""Tests for `app.optimizer.advisors.skill_advisor`.

The test that matters most here is
`test_same_type_same_tier_skills_can_rank_differently`: the review of
the original Module 3 cut correctly flagged that scoring by
`skill_type`/`tier` alone meant Multishot, Ricochet, and Attack Up (all
OFFENSIVE, all tier 3) were indistinguishable — the engine could tell
"an offensive skill is good for this build" but not "*this* offensive
skill is better than *that* one." Module 3.1's marginal-build-simulation
model (`app.optimizer.simulator.apply_skill` +
`app.optimizer.objectives.ObjectiveProfile`) is what fixes that.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.models import (
    EffectType,
    Hero,
    HeroClass,
    Rarity,
    Skill,
    SkillEffect,
    SkillType,
    UserAccount,
    UserHeroOwnership,
)
from app.optimizer import objectives
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
def multishot_skill(db: Session) -> Skill:
    instance = Skill(name="Multishot", skill_type=SkillType.OFFENSIVE, tier=3)
    instance.effects = [SkillEffect(effect_type=EffectType.PROJECTILE_COUNT, value=1.0)]
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def ricochet_skill(db: Session) -> Skill:
    instance = Skill(name="Ricochet", skill_type=SkillType.OFFENSIVE, tier=3)
    instance.effects = [SkillEffect(effect_type=EffectType.BOUNCE_COUNT, value=2.0)]
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def attack_up_skill(db: Session) -> Skill:
    instance = Skill(name="Attack Up", skill_type=SkillType.OFFENSIVE, tier=3)
    instance.effects = [SkillEffect(effect_type=EffectType.ATTACK_SPEED_MULTIPLIER, value=0.15)]
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def no_effect_skill(db: Session) -> Skill:
    """A catalog skill with no structured effects yet — the honest
    tier-only fallback case."""
    instance = Skill(name="Mystery Perk", skill_type=SkillType.OFFENSIVE, tier=3)
    db.add(instance)
    db.commit()
    return instance


def _fresh_build() -> BuildContext:
    return _context(
        attack=500.0,
        defense=50.0,
        max_hp=800.0,
        attack_speed=0.5,
        crit_chance=0.2,
        crit_damage=1.5,
        combat_power=1000.0,
        recommended_combat_power=1000.0,
    )


# --- Pure `score_skill`/`advise` -------------------------------------------


def test_same_type_same_tier_skills_can_rank_differently(
    multishot_skill: Skill, ricochet_skill: Skill, attack_up_skill: Skill
) -> None:
    context = _fresh_build()

    scores = {
        skill.name: skill_advisor.score_skill(context, skill).score
        for skill in (multishot_skill, ricochet_skill, attack_up_skill)
    }

    assert len(set(scores.values())) == 3, (
        f"expected three distinct scores for three same-type, same-tier skills, got {scores}"
    )


def test_skill_with_no_effects_falls_back_to_tier_only_score(no_effect_skill: Skill) -> None:
    scored = skill_advisor.score_skill(_fresh_build(), no_effect_skill)

    assert scored.score == 30.0  # SKILL_TIER_BASE_VALUE (10.0) * tier (3), zero marginal gain
    assert "tier-only" in scored.reasons[-1].lower()


def test_boss_objective_favors_single_target_skill(
    ricochet_skill: Skill, attack_up_skill: Skill
) -> None:
    result = skill_advisor.advise(
        _fresh_build(), [ricochet_skill, attack_up_skill], objectives.BOSS
    )
    assert result.recommended.option is attack_up_skill


def test_farm_objective_favors_aoe_skill_over_the_same_build(
    ricochet_skill: Skill, attack_up_skill: Skill
) -> None:
    result = skill_advisor.advise(
        _fresh_build(), [ricochet_skill, attack_up_skill], objectives.FARM
    )
    assert result.recommended.option is ricochet_skill


def test_boss_and_farm_objectives_flip_the_recommendation_for_the_same_build(
    ricochet_skill: Skill, attack_up_skill: Skill
) -> None:
    """The Module 3.1 analogue of Module 3's build-flip test: this time
    the build is held constant and the *objective* changes, which is
    exactly the "boss fight vs. farming" distinction the review asked
    for."""

    context = _fresh_build()
    candidates = [ricochet_skill, attack_up_skill]

    boss_result = skill_advisor.advise(context, candidates, objectives.BOSS)
    farm_result = skill_advisor.advise(context, candidates, objectives.FARM)

    assert boss_result.recommended.option is not farm_result.recommended.option


def test_existing_selected_skill_reduces_marginal_value_of_a_similar_new_one(
    multishot_skill: Skill,
) -> None:
    """An account that already has one PROJECTILE_COUNT skill equipped
    (`projectile_count` baseline of 2.0 instead of 1.0) should value a
    *second* one less — diminishing returns, and the concrete mechanism
    by which "already selected skills" changes a recommendation, per the
    review."""

    fresh = _fresh_build()
    already_stacked = _context(**{**vars(fresh), "projectile_count": 2.0})

    fresh_score = skill_advisor.score_skill(fresh, multishot_skill, objectives.FARM).score
    stacked_score = skill_advisor.score_skill(
        already_stacked, multishot_skill, objectives.FARM
    ).score

    assert stacked_score < fresh_score


def test_advise_ranks_best_option_first(
    multishot_skill: Skill, ricochet_skill: Skill, attack_up_skill: Skill
) -> None:
    result = skill_advisor.advise(
        _fresh_build(), [multishot_skill, ricochet_skill, attack_up_skill]
    )
    assert [scored.score for scored in result.ranked] == sorted(
        (scored.score for scored in result.ranked), reverse=True
    )


def test_advise_requires_at_least_one_candidate() -> None:
    with pytest.raises(ValueError):
        skill_advisor.advise(_context(), [])


def test_advise_breaks_score_ties_deterministically_by_skill_id(db: Session) -> None:
    """Two skills with genuinely identical effects (and therefore
    identical scores) must not have their relative order depend on
    which order they were submitted in."""

    first = Skill(name="Twin A", skill_type=SkillType.OFFENSIVE, tier=2)
    first.effects = [SkillEffect(effect_type=EffectType.PROJECTILE_COUNT, value=1.0)]
    second = Skill(name="Twin B", skill_type=SkillType.OFFENSIVE, tier=2)
    second.effects = [SkillEffect(effect_type=EffectType.PROJECTILE_COUNT, value=1.0)]
    db.add_all([first, second])
    db.commit()
    assert first.id < second.id

    context = _fresh_build()
    forward = skill_advisor.advise(context, [first, second])
    backward = skill_advisor.advise(context, [second, first])

    assert forward.recommended.option.id == backward.recommended.option.id == first.id


# --- DB-aware `advise_for_account` -----------------------------------------


@pytest.fixture()
def account_with_hero(db: Session) -> UserAccount:
    account = UserAccount(display_name="carl")
    hero_row = Hero(
        name="Hero",
        hero_class=HeroClass.WARRIOR,
        rarity=Rarity.EPIC,
        base_attack=500.0,
        base_defense=50.0,
        base_hp=800.0,
        base_attack_speed=0.5,
    )
    db.add_all([account, hero_row])
    db.commit()
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero_row.id, level=1, is_active=True))
    db.commit()
    return account


def test_advise_for_account_respects_objective_parameter(
    db: Session,
    account_with_hero: UserAccount,
    ricochet_skill: Skill,
    attack_up_skill: Skill,
) -> None:
    candidate_ids = [ricochet_skill.id, attack_up_skill.id]

    boss_result = skill_advisor.advise_for_account(
        db, account_with_hero.id, candidate_ids, "boss"
    )
    farm_result = skill_advisor.advise_for_account(
        db, account_with_hero.id, candidate_ids, "farm"
    )

    assert boss_result.recommended.option.id == attack_up_skill.id
    assert farm_result.recommended.option.id == ricochet_skill.id


def test_advise_for_account_defaults_to_balanced_objective(
    db: Session, account_with_hero: UserAccount, multishot_skill: Skill
) -> None:
    result = skill_advisor.advise_for_account(db, account_with_hero.id, [multishot_skill.id])
    assert result.recommended.option.id == multishot_skill.id


def test_advise_for_account_raises_not_found_for_unknown_objective(
    db: Session, account_with_hero: UserAccount, multishot_skill: Skill
) -> None:
    with pytest.raises(NotFoundError):
        skill_advisor.advise_for_account(
            db, account_with_hero.id, [multishot_skill.id], "nonsense"
        )


def test_advise_for_account_raises_not_found_for_missing_account(
    db: Session, multishot_skill: Skill
) -> None:
    with pytest.raises(NotFoundError):
        skill_advisor.advise_for_account(db, 999999, [multishot_skill.id])


def test_advise_for_account_raises_not_found_for_missing_skill(
    db: Session, account_with_hero: UserAccount
) -> None:
    with pytest.raises(NotFoundError):
        skill_advisor.advise_for_account(db, account_with_hero.id, [999999])


def test_advise_for_account_deduplicates_candidate_ids(
    db: Session,
    account_with_hero: UserAccount,
    multishot_skill: Skill,
    ricochet_skill: Skill,
) -> None:
    result = skill_advisor.advise_for_account(
        db,
        account_with_hero.id,
        [multishot_skill.id, multishot_skill.id, ricochet_skill.id],
    )
    assert len(result.ranked) == 2
