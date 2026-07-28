"""Upgrade Advisor: across every item an account owns, finds the single
best investment of its current gold — never a static "always upgrade
your weapon first" rule.

Each candidate assumes the account's *entire* current gold goes toward
that one item alone (not a simultaneous multi-item purchase plan — the
ranking answers "if I had to pick one thing to put my gold into right
now, which gives the most build improvement," which is exactly the
question the spec's example asks). An item that can't be leveled up at
all with the account's current gold is never even scored, and one that
*can* be afforded but wouldn't meaningfully improve the build (marginal
gain at or below zero) is filtered out afterward — this advisor would
rather recommend nothing than a bad investment.

Uses the exact same mechanism as Gear Advisor: `score_upgrade` builds a
hypothetical `BuildContext` via `simulator.replace_contribution`
(before = the item at its current level, after = the item at the
highest level the account can currently afford) and scores the marginal
`ObjectiveProfile` gain, expressed as a percentage of the build's
current objective score — "expected build improvement %."

Only the account's *active/equipped* item per category is ever a
candidate — a bench hero, an unequipped weapon, an un-slotted rune are
never considered. This isn't a minor filter: `replace_contribution`'s
"before" side only makes sense as a *subtraction from the current
BuildContext*, and `build_context()` only folds in what's actually
equipped/active in the first place. An unequipped item's "current
contribution" was never added to the context to begin with, so
subtracting it and adding the upgraded amount doesn't simulate "upgrade
this owned-but-unequipped item" at all — it silently stacks the
item's own level-delta directly onto whatever *is* currently equipped,
which corresponds to no real action a player can take. Recommending
"upgrade and equip this bench item" would need to compose an upgrade
with a Gear Advisor-style swap (a genuinely different simulation this
advisor doesn't attempt yet), not just widen which candidates it
scores under the current formula.
"""

from __future__ import annotations

import enum
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.models import Amulet, Armor, Hero, Pet, Ring, Rune, UserAccount, Weapon
from app.optimizer import explanations, objectives, simulator, weights
from app.optimizer.context import (
    BuildContext,
    armor_contribution,
    build_context,
    hero_contribution,
    rune_effect_contribution,
    stat_item_contribution,
    weapon_contribution,
)
from app.optimizer.objectives import ObjectiveProfile
from app.optimizer.results import AdvisorResult, ScoredOption
from app.services import account_service

_Candidate = tuple["UpgradeOption", dict[str, float], dict[str, float]]


class UpgradeCategory(enum.StrEnum):
    HERO = "hero"
    WEAPON = "weapon"
    ARMOR = "armor"
    RING = "ring"
    AMULET = "amulet"
    PET = "pet"
    RUNE = "rune"


@dataclass(frozen=True)
class UpgradeOption:
    """One owned item the Upgrade Advisor is proposing to level up."""

    category: UpgradeCategory
    ownership_id: int
    catalog_id: int
    name: str
    from_level: int
    to_level: int
    gold_cost: float


def max_affordable_levels(current_level: int, gold: float) -> tuple[int, float]:
    """How many levels of `BASE_UPGRADE_COST_PER_LEVEL * level` cost the
    account can afford right now, capped at
    `MAX_UPGRADE_LEVELS_CONSIDERED`, and the total gold that would cost.
    Returns `(0, 0.0)` if even a single level isn't affordable."""

    levels = 0
    total_cost = 0.0
    while levels < weights.MAX_UPGRADE_LEVELS_CONSIDERED:
        next_level_cost = weights.BASE_UPGRADE_COST_PER_LEVEL * (current_level + levels)
        if total_cost + next_level_cost > gold:
            break
        total_cost += next_level_cost
        levels += 1
    return levels, total_cost


def _hero_contribution_fn(hero: Hero) -> Callable[[int], dict[str, float]]:
    return lambda level: hero_contribution(hero, level)


def _weapon_contribution_fn(weapon: Weapon, star_level: int) -> Callable[[int], dict[str, float]]:
    return lambda level: weapon_contribution(weapon, level, star_level)


def _armor_contribution_fn(armor: Armor, star_level: int) -> Callable[[int], dict[str, float]]:
    return lambda level: armor_contribution(armor, level, star_level)


def _ring_contribution_fn(ring: Ring) -> Callable[[int], dict[str, float]]:
    return lambda level: stat_item_contribution(ring.primary_stat, ring.primary_stat_value, level)


def _amulet_contribution_fn(amulet: Amulet) -> Callable[[int], dict[str, float]]:
    return lambda level: stat_item_contribution(
        amulet.primary_stat, amulet.primary_stat_value, level
    )


def _pet_contribution_fn(pet: Pet) -> Callable[[int], dict[str, float]]:
    return lambda level: stat_item_contribution(pet.bonus_stat, pet.bonus_stat_value, level)


def _rune_contribution_fn(rune: Rune) -> Callable[[int], dict[str, float]]:
    return lambda level: rune_effect_contribution(rune, level)


def _affordable_candidate(
    category: UpgradeCategory,
    ownership_id: int,
    catalog_id: int,
    name: str,
    current_level: int,
    gold: float,
    contribution_at: Callable[[int], dict[str, float]],
) -> _Candidate | None:
    levels, cost = max_affordable_levels(current_level, gold)
    if levels < 1:
        return None
    option = UpgradeOption(
        category=category,
        ownership_id=ownership_id,
        catalog_id=catalog_id,
        name=name,
        from_level=current_level,
        to_level=current_level + levels,
        gold_cost=cost,
    )
    return option, contribution_at(current_level), contribution_at(current_level + levels)


def _hero_candidates(account: UserAccount, gold: float) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for ownership in account.heroes:
        if not ownership.is_active:
            continue
        candidate = _affordable_candidate(
            UpgradeCategory.HERO,
            ownership.id,
            ownership.hero_id,
            ownership.hero.name,
            ownership.level,
            gold,
            _hero_contribution_fn(ownership.hero),
        )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _weapon_candidates(account: UserAccount, gold: float) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for ownership in account.weapons:
        if not ownership.is_equipped:
            continue
        candidate = _affordable_candidate(
            UpgradeCategory.WEAPON,
            ownership.id,
            ownership.weapon_id,
            ownership.weapon.name,
            ownership.level,
            gold,
            _weapon_contribution_fn(ownership.weapon, ownership.star_level),
        )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _armor_candidates(account: UserAccount, gold: float) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for ownership in account.armor_pieces:
        if not ownership.is_equipped:
            continue
        candidate = _affordable_candidate(
            UpgradeCategory.ARMOR,
            ownership.id,
            ownership.armor_id,
            ownership.armor.name,
            ownership.level,
            gold,
            _armor_contribution_fn(ownership.armor, ownership.star_level),
        )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _ring_candidates(account: UserAccount, gold: float) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for ownership in account.rings:
        if not ownership.is_equipped:
            continue
        candidate = _affordable_candidate(
            UpgradeCategory.RING,
            ownership.id,
            ownership.ring_id,
            ownership.ring.name,
            ownership.level,
            gold,
            _ring_contribution_fn(ownership.ring),
        )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _amulet_candidates(account: UserAccount, gold: float) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for ownership in account.amulets:
        if not ownership.is_equipped:
            continue
        candidate = _affordable_candidate(
            UpgradeCategory.AMULET,
            ownership.id,
            ownership.amulet_id,
            ownership.amulet.name,
            ownership.level,
            gold,
            _amulet_contribution_fn(ownership.amulet),
        )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _pet_candidates(account: UserAccount, gold: float) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for ownership in account.pets:
        if not ownership.is_active:
            continue
        candidate = _affordable_candidate(
            UpgradeCategory.PET,
            ownership.id,
            ownership.pet_id,
            ownership.pet.name,
            ownership.level,
            gold,
            _pet_contribution_fn(ownership.pet),
        )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _rune_candidates(account: UserAccount, gold: float) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for ownership in account.runes:
        if not ownership.is_equipped:
            continue
        candidate = _affordable_candidate(
            UpgradeCategory.RUNE,
            ownership.id,
            ownership.rune_id,
            ownership.rune.name,
            ownership.level,
            gold,
            _rune_contribution_fn(ownership.rune),
        )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def score_upgrade(
    context: BuildContext,
    option: UpgradeOption,
    current_contribution: dict[str, float],
    upgraded_contribution: dict[str, float],
    objective: ObjectiveProfile = objectives.BALANCED,
) -> ScoredOption[UpgradeOption]:
    """Score one affordable upgrade option. Pure function — no I/O — so
    it's directly unit-testable without a database. `score` is the
    expected percentage build improvement, matching how the advisor
    reports it to the player."""

    simulated = simulator.replace_contribution(
        context, before=current_contribution, after=upgraded_contribution
    )
    before_score = objective.evaluate(context)
    after_score = objective.evaluate(simulated)
    gain = after_score - before_score
    gain_pct = (gain / before_score * 100.0) if before_score else 0.0

    changed = explanations.changed_fields(context, simulated)
    base_label = (
        f"{option.name}: level {option.from_level} -> {option.to_level} "
        f"for {option.gold_cost:.0f} gold"
    )
    reasons = explanations.build_reasons(base_label, changed, objective.name, gain)
    summary = (
        f"Spend {option.gold_cost:.0f} gold to upgrade {option.name} "
        f"(level {option.from_level} -> {option.to_level}): "
        f"expected build improvement {gain_pct:+.1f}%."
    )

    return ScoredOption(option=option, score=gain_pct, summary=summary, reasons=reasons)


def advise(
    context: BuildContext,
    candidates: Sequence[_Candidate],
    objective: ObjectiveProfile = objectives.BALANCED,
) -> AdvisorResult[UpgradeOption]:
    """Rank every affordable upgrade candidate, best first. Ties break on
    `(category, catalog_id, ownership_id)` ascending — unlike every
    other advisor's single-category ranking, `catalog_id` alone is not
    unique here (a `Hero` and a `Weapon` can share catalog id 1), so
    breaking ties on it alone would be non-deterministic across
    categories; `ownership_id` is the final, always-unique tiebreaker."""

    if not candidates:
        raise ValueError("advise() requires at least one candidate upgrade")

    scored = [
        score_upgrade(context, option, current, upgraded, objective)
        for option, current, upgraded in candidates
    ]
    scored.sort(
        key=lambda scored_option: (
            -scored_option.score,
            scored_option.option.category.value,
            scored_option.option.catalog_id,
            scored_option.option.ownership_id,
        )
    )
    return AdvisorResult(ranked=tuple(scored))


def advise_for_account(
    db: Session, account_id: int, objective_name: str = "balanced"
) -> AdvisorResult[UpgradeOption]:
    """DB-aware entry point: loads the account's build and every
    *currently active/equipped* item across all seven ownable
    categories that it can currently afford to level up, filters out
    anything that wouldn't actually improve the build, and delegates to
    the pure `advise` above. Raises `NotFoundError` (a 404) if nothing
    is affordable, or if everything affordable is worthless — both
    real, valid states, not error conditions the caller did anything
    wrong to reach."""

    account = account_service.get_account_detail(db, account_id)
    context = build_context(account)
    objective = objectives.resolve(objective_name)

    candidates: list[_Candidate] = [
        *_hero_candidates(account, account.gold),
        *_weapon_candidates(account, account.gold),
        *_armor_candidates(account, account.gold),
        *_ring_candidates(account, account.gold),
        *_amulet_candidates(account, account.gold),
        *_pet_candidates(account, account.gold),
        *_rune_candidates(account, account.gold),
    ]
    if not candidates:
        raise NotFoundError(f"Account {account_id} cannot afford to upgrade anything right now")

    result = advise(context, candidates, objective)
    worthwhile = tuple(scored for scored in result.ranked if scored.score > 0)
    if not worthwhile:
        raise NotFoundError(f"Account {account_id} has no upgrade worth making right now")
    return AdvisorResult(ranked=worthwhile)
