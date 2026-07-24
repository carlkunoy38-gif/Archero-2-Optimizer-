"""Gear Advisor: compares an account's *owned* weapons/armor/rings/
amulets/pets in one category and recommends which to equip — never a
static tier list.

Candidates here always come from the account's own ownership rows,
never a client-submitted id list the way `skill_advisor` takes
candidate skill ids: there is no "equip an item you don't have" in this
game, so "what could I equip" is entirely determined by "what do I
own." Armor is additionally scoped by `ArmorSlot` — a helmet and a pair
of boots don't compete for the same equip slot, matching how
`equipment_service.equip_armor` itself only ever replaces whatever else
was equipped in the *same* slot.

Scoring reuses the exact same mechanism as `skill_advisor`, just with
`simulator.replace_contribution` swapping one item's contribution for
another's instead of `simulator.apply_skill` adding one on top:
`score_item` builds a hypothetical `BuildContext` as if this candidate
were equipped in place of whatever currently is, and scores that
hypothetical context directly with the chosen `ObjectiveProfile` — so
"keep what I have" and "switch to this" are directly comparable
numbers, not a diff against an arbitrary baseline the way skills need a
tier floor (gear items already have real numeric stats; there is no
"no effects yet" gap to fill with one).
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.models import ArmorSlot, UserAccount
from app.optimizer import explanations, objectives, simulator
from app.optimizer.context import (
    BuildContext,
    armor_contribution,
    build_context,
    stat_item_contribution,
    weapon_contribution,
)
from app.optimizer.objectives import ObjectiveProfile
from app.optimizer.results import AdvisorResult, ScoredOption
from app.services import account_service


class GearCategory(enum.StrEnum):
    WEAPON = "weapon"
    ARMOR = "armor"
    RING = "ring"
    AMULET = "amulet"
    PET = "pet"


@dataclass(frozen=True)
class GearOption:
    """One owned item the Gear Advisor can recommend equipping."""

    category: GearCategory
    ownership_id: int
    catalog_id: int
    name: str
    is_currently_equipped: bool


def score_item(
    context: BuildContext,
    option: GearOption,
    current_contribution: dict[str, float],
    candidate_contribution: dict[str, float],
    objective: ObjectiveProfile = objectives.BALANCED,
) -> ScoredOption[GearOption]:
    """Score one owned item as a candidate to equip. Pure function — no
    I/O — so it's directly unit-testable without a database."""

    simulated = simulator.replace_contribution(
        context, before=current_contribution, after=candidate_contribution
    )
    score = objective.evaluate(simulated)
    gain = score - objective.evaluate(context)

    changed = explanations.changed_fields(context, simulated)
    status = "currently equipped" if option.is_currently_equipped else "in inventory"
    reasons = explanations.build_reasons(
        f"{option.name} ({status})", changed, objective.name, gain
    )
    summary = explanations.build_summary(option.name, changed, objective.name, gain)

    return ScoredOption(option=option, score=score, summary=summary, reasons=reasons)


def advise(
    context: BuildContext,
    candidates: Sequence[tuple[GearOption, dict[str, float]]],
    current_contribution: dict[str, float],
    objective: ObjectiveProfile = objectives.BALANCED,
) -> AdvisorResult[GearOption]:
    """Rank every owned candidate in one category/slot, best first.

    `candidates` pairs each `GearOption` with its own contribution dict
    (computed at that item's *own* owned level/star — see
    `app.optimizer.context.weapon_contribution` and friends). Ties break
    on catalog id ascending, same as every other advisor."""

    if not candidates:
        raise ValueError("advise() requires at least one candidate item")

    scored = [
        score_item(context, option, current_contribution, contribution, objective)
        for option, contribution in candidates
    ]
    scored.sort(key=lambda scored_option: (-scored_option.score, scored_option.option.catalog_id))
    return AdvisorResult(ranked=tuple(scored))


def _weapon_candidates(
    account: UserAccount,
) -> tuple[list[tuple[GearOption, dict[str, float]]], dict[str, float]]:
    candidates: list[tuple[GearOption, dict[str, float]]] = []
    current: dict[str, float] = {}
    for ownership in account.weapons:
        contribution = weapon_contribution(ownership.weapon, ownership.level, ownership.star_level)
        option = GearOption(
            category=GearCategory.WEAPON,
            ownership_id=ownership.id,
            catalog_id=ownership.weapon_id,
            name=ownership.weapon.name,
            is_currently_equipped=ownership.is_equipped,
        )
        candidates.append((option, contribution))
        if ownership.is_equipped:
            current = contribution
    return candidates, current


def _armor_candidates(
    account: UserAccount, slot: ArmorSlot
) -> tuple[list[tuple[GearOption, dict[str, float]]], dict[str, float]]:
    candidates: list[tuple[GearOption, dict[str, float]]] = []
    current: dict[str, float] = {}
    for ownership in account.armor_pieces:
        if ownership.slot != slot:
            continue
        contribution = armor_contribution(ownership.armor, ownership.level, ownership.star_level)
        option = GearOption(
            category=GearCategory.ARMOR,
            ownership_id=ownership.id,
            catalog_id=ownership.armor_id,
            name=ownership.armor.name,
            is_currently_equipped=ownership.is_equipped,
        )
        candidates.append((option, contribution))
        if ownership.is_equipped:
            current = contribution
    return candidates, current


def _ring_candidates(
    account: UserAccount,
) -> tuple[list[tuple[GearOption, dict[str, float]]], dict[str, float]]:
    candidates: list[tuple[GearOption, dict[str, float]]] = []
    current: dict[str, float] = {}
    for ownership in account.rings:
        contribution = stat_item_contribution(
            ownership.ring.primary_stat, ownership.ring.primary_stat_value, ownership.level
        )
        option = GearOption(
            category=GearCategory.RING,
            ownership_id=ownership.id,
            catalog_id=ownership.ring_id,
            name=ownership.ring.name,
            is_currently_equipped=ownership.is_equipped,
        )
        candidates.append((option, contribution))
        if ownership.is_equipped:
            current = contribution
    return candidates, current


def _amulet_candidates(
    account: UserAccount,
) -> tuple[list[tuple[GearOption, dict[str, float]]], dict[str, float]]:
    candidates: list[tuple[GearOption, dict[str, float]]] = []
    current: dict[str, float] = {}
    for ownership in account.amulets:
        contribution = stat_item_contribution(
            ownership.amulet.primary_stat, ownership.amulet.primary_stat_value, ownership.level
        )
        option = GearOption(
            category=GearCategory.AMULET,
            ownership_id=ownership.id,
            catalog_id=ownership.amulet_id,
            name=ownership.amulet.name,
            is_currently_equipped=ownership.is_equipped,
        )
        candidates.append((option, contribution))
        if ownership.is_equipped:
            current = contribution
    return candidates, current


def _pet_candidates(
    account: UserAccount,
) -> tuple[list[tuple[GearOption, dict[str, float]]], dict[str, float]]:
    candidates: list[tuple[GearOption, dict[str, float]]] = []
    current: dict[str, float] = {}
    for ownership in account.pets:
        contribution = stat_item_contribution(
            ownership.pet.bonus_stat, ownership.pet.bonus_stat_value, ownership.level
        )
        option = GearOption(
            category=GearCategory.PET,
            ownership_id=ownership.id,
            catalog_id=ownership.pet_id,
            name=ownership.pet.name,
            is_currently_equipped=ownership.is_active,
        )
        candidates.append((option, contribution))
        if ownership.is_active:
            current = contribution
    return candidates, current


def advise_for_account(
    db: Session,
    account_id: int,
    category: GearCategory,
    armor_slot: ArmorSlot | None = None,
    objective_name: str = "balanced",
) -> AdvisorResult[GearOption]:
    """DB-aware entry point: loads the account's build and its owned
    items in `category` (raising `NotFoundError` for a missing account,
    an unknown objective name, or no owned items to compare), then
    delegates to the pure `advise` above."""

    account = account_service.get_account_detail(db, account_id)
    build = build_context(account)
    objective = objectives.resolve(objective_name)

    if category is GearCategory.WEAPON:
        candidates, current = _weapon_candidates(account)
    elif category is GearCategory.ARMOR:
        if armor_slot is None:
            raise NotFoundError("armor_slot is required when category is 'armor'")
        candidates, current = _armor_candidates(account, armor_slot)
    elif category is GearCategory.RING:
        candidates, current = _ring_candidates(account)
    elif category is GearCategory.AMULET:
        candidates, current = _amulet_candidates(account)
    else:
        candidates, current = _pet_candidates(account)

    if not candidates:
        raise NotFoundError(f"Account {account_id} owns no {category.value} to compare")

    return advise(build, candidates, current, objective)
