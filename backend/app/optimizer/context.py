"""BuildContext: a pure snapshot of one account's current build,
aggregated from its active hero, equipped gear, socketed runes, active
pet, and already-equipped skills' structured effects (`SkillEffect`) —
the one thing every advisor scores candidates against.

Building one requires no I/O of its own: `build_context` takes an
already-loaded `UserAccount` ORM object (see
`app.repositories.account_repository.get_account_with_detail`, which
eager-loads everything accessed below) and returns a plain, immutable
dataclass. Nothing downstream of this function ever touches a database
session, a `Hero`/`Weapon`/`Armor`/... row, or SQLAlchemy at all —
which is exactly what makes the engine reusable outside a web request
(a CLI, a batch job, or a future screenshot-analysis pipeline that
builds a `BuildContext` some other way entirely).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.models import (
    Armor,
    EffectType,
    Hero,
    RuneType,
    Skill,
    StatType,
    UserAccount,
    Weapon,
)
from app.optimizer import weights

#: Which BuildContext field each ring/amulet StatType feeds into. Not
#: every StatType a rune/pet could theoretically grant maps to a field
#: tracked below (e.g. there's no separate "resource_gain" breakdown by
#: source) — entries absent here are silently ignored rather than
#: raising, since new StatType members may be added to the catalog
#: without every consumer needing to handle them immediately.
_STAT_TYPE_FIELD: dict[StatType, str] = {
    StatType.ATTACK: "attack",
    StatType.DEFENSE: "defense",
    StatType.HEALTH: "max_hp",
    StatType.CRIT_CHANCE: "crit_chance",
    StatType.CRIT_DAMAGE: "crit_damage",
    StatType.ATTACK_SPEED: "attack_speed",
    StatType.MOVEMENT_SPEED: "movement_speed",
    StatType.LIFE_STEAL: "life_steal",
    StatType.DODGE: "dodge",
    StatType.RESOURCE_GAIN: "resource_gain",
}

#: Which BuildContext field a `SkillEffect.effect_type` feeds into.
#: Shared between `build_context` (folding an account's already-equipped
#: skills' effects into the baseline) and
#: `app.optimizer.simulator.apply_skill` (projecting one *candidate*
#: skill's effects onto a copy of the context) — both need the exact
#: same mapping, so it lives here rather than being duplicated.
_EFFECT_TYPE_FIELD: dict[EffectType, str] = {
    EffectType.PROJECTILE_COUNT: "projectile_count",
    EffectType.BOUNCE_COUNT: "bounce_count",
    EffectType.ATTACK_SPEED_MULTIPLIER: "attack_speed",
    EffectType.CRIT_CHANCE_BONUS: "crit_chance",
    EffectType.CRIT_DAMAGE_BONUS: "crit_damage",
    EffectType.DEFENSE_BONUS: "defense",
    EffectType.MAX_HP_BONUS: "max_hp",
    EffectType.DODGE_BONUS: "dodge",
    EffectType.MOVEMENT_SPEED_BONUS: "movement_speed",
    EffectType.RESOURCE_GAIN_BONUS: "resource_gain",
    EffectType.LIFE_STEAL_BONUS: "life_steal",
}


@dataclass(frozen=True)
class BuildContext:
    """An immutable snapshot of one account's aggregated build stats.

    Every numeric field is a sum across whatever is currently
    active/equipped — not a per-item breakdown. Advisors that need to
    compare *individual* gear options (the Gear Advisor) or a
    hypothetical higher level (the Upgrade Advisor) don't read fields
    off of one shared context the way the Skill Advisor does — they use
    `app.optimizer.simulator.replace_contribution` to swap one item's
    contribution for another's on a copy of this context, built from
    the same per-item contribution functions below
    (`weapon_contribution`, `armor_contribution`, ...).
    """

    account_id: int
    hero_level: int
    attack: float
    defense: float
    max_hp: float
    attack_speed: float
    crit_chance: float
    crit_damage: float
    movement_speed: float
    life_steal: float
    dodge: float
    resource_gain: float
    combat_power: float
    recommended_combat_power: float | None

    #: Extra simultaneous projectiles/bounces per attack, from skill
    #: effects (`EffectType.PROJECTILE_COUNT` / `BOUNCE_COUNT`). `1.0` is
    #: the baseline every build has (one projectile with no skills) —
    #: `bounce_count` has no such baseline, since bouncing is purely
    #: additive from skills. See `engine.aoe_score`.
    projectile_count: float = 1.0
    bounce_count: float = 0.0

    #: IDs of the skills the account already has equipped (a non-null
    #: `equipped_slot`, not merely unlocked). Their effects are already
    #: folded into the numeric fields above by `build_context` — this is
    #: for advisors that want to *explain* a recommendation in terms of
    #: what's already selected (e.g. "you already have two projectile
    #: skills, so a third is worth less"), not for scoring math itself.
    selected_skill_ids: frozenset[int] = field(default_factory=frozenset)

    @property
    def power_gap_ratio(self) -> float:
        """`combat_power / recommended_combat_power` for the account's
        current chapter: <1 means under-powered for it, >1 over-powered.
        Defaults to 1.0 (neutral — neither pushes advice toward survival
        nor toward aggression) when no current chapter is set."""

        if not self.recommended_combat_power:
            return 1.0
        return self.combat_power / self.recommended_combat_power


def _level_multiplier(level: int) -> float:
    return 1.0 + max(level - 1, 0) * weights.LEVEL_GROWTH_RATE


def _star_multiplier(star_level: int) -> float:
    return 1.0 + star_level * weights.STAR_LEVEL_BONUS


# --- Per-item contribution functions ---------------------------------------
#
# Pure functions from "a catalog row at a given level/star" to "how much it
# adds to which BuildContext field." `build_context` below calls these for
# whatever is *currently* equipped/active, but they take a level/star rather
# than an ownership row specifically so the same math also answers "how much
# would a *different* level, or a *candidate item the account isn't
# currently using*, contribute" — which is exactly what the Gear Advisor
# (comparing owned-but-unequipped items) and the Upgrade Advisor (comparing
# an item's current level to a hypothetical higher one) need, via
# `app.optimizer.simulator.replace_contribution`. Extracting this out of
# `build_context`'s loop bodies means both call sites use the exact same
# formula — there is no second copy of "how much attack does a weapon at
# level 5, 2 stars actually add" anywhere in the codebase.


def hero_contribution(hero: Hero, level: int) -> dict[str, float]:
    factor = _level_multiplier(level)
    return {
        "attack": hero.base_attack * factor,
        "defense": hero.base_defense * factor,
        "max_hp": hero.base_hp * factor,
        "attack_speed": hero.base_attack_speed,
    }


def weapon_contribution(weapon: Weapon, level: int, star_level: int) -> dict[str, float]:
    factor = _level_multiplier(level) * _star_multiplier(star_level)
    return {
        "attack": weapon.base_damage * factor,
        "attack_speed": weapon.base_attack_speed,
        "crit_chance": weapon.crit_chance_bonus,
    }


def armor_contribution(armor: Armor, level: int, star_level: int) -> dict[str, float]:
    factor = _level_multiplier(level) * _star_multiplier(star_level)
    return {
        "defense": armor.base_defense * factor,
        "max_hp": armor.base_hp * factor,
    }


def stat_item_contribution(stat_type: StatType, value: float, level: int) -> dict[str, float]:
    """Shared math for any single-stat item — a ring/amulet's
    `primary_stat`/`primary_stat_value` or a pet's `bonus_stat`/
    `bonus_stat_value` are the same shape (one `StatType`, one magnitude,
    scaled by level), so all three call this rather than each having their
    own copy."""

    stat_field = _STAT_TYPE_FIELD.get(stat_type)
    if stat_field is None:
        return {}
    return {stat_field: value * _level_multiplier(level)}


def rune_contribution(rune_type: RuneType, effect_value: float, level: int) -> dict[str, float]:
    stat_field = weights.RUNE_TYPE_STAT_FIELD.get(rune_type)
    if stat_field is None:
        return {}
    return {stat_field: effect_value * _level_multiplier(level)}


def skill_effect_contribution(skill: Skill) -> dict[str, float]:
    """Skills have no level — every `SkillEffect` on the row applies at full
    value. Used both for an account's already-equipped skills
    (`build_context` below) and for a *candidate* skill
    (`app.optimizer.simulator.apply_skill`)."""

    totals: dict[str, float] = {}
    for effect in skill.effects:
        effect_field = _EFFECT_TYPE_FIELD.get(effect.effect_type)
        if effect_field is None:
            continue
        totals[effect_field] = totals.get(effect_field, 0.0) + effect.value
    return totals


def build_context(account: UserAccount) -> BuildContext:
    totals: dict[str, float] = dict.fromkeys(
        set(_STAT_TYPE_FIELD.values()) | set(_EFFECT_TYPE_FIELD.values()), 0.0
    )
    totals["projectile_count"] = 1.0

    def _add(contribution: dict[str, float]) -> None:
        for contribution_field, value in contribution.items():
            totals[contribution_field] = totals.get(contribution_field, 0.0) + value

    active_hero = next((h for h in account.heroes if h.is_active), None)
    hero_level = active_hero.level if active_hero is not None else 0
    if active_hero is not None:
        _add(hero_contribution(active_hero.hero, active_hero.level))

    equipped_weapon = next((w for w in account.weapons if w.is_equipped), None)
    if equipped_weapon is not None:
        _add(
            weapon_contribution(
                equipped_weapon.weapon, equipped_weapon.level, equipped_weapon.star_level
            )
        )

    for armor_ownership in account.armor_pieces:
        if not armor_ownership.is_equipped:
            continue
        _add(
            armor_contribution(
                armor_ownership.armor, armor_ownership.level, armor_ownership.star_level
            )
        )

    for ring_ownership in account.rings:
        if not ring_ownership.is_equipped:
            continue
        _add(
            stat_item_contribution(
                ring_ownership.ring.primary_stat,
                ring_ownership.ring.primary_stat_value,
                ring_ownership.level,
            )
        )

    for amulet_ownership in account.amulets:
        if not amulet_ownership.is_equipped:
            continue
        _add(
            stat_item_contribution(
                amulet_ownership.amulet.primary_stat,
                amulet_ownership.amulet.primary_stat_value,
                amulet_ownership.level,
            )
        )

    active_pet = next((p for p in account.pets if p.is_active), None)
    if active_pet is not None:
        _add(
            stat_item_contribution(
                active_pet.pet.bonus_stat, active_pet.pet.bonus_stat_value, active_pet.level
            )
        )

    for rune_ownership in account.runes:
        if not rune_ownership.is_equipped:
            continue
        _add(
            rune_contribution(
                rune_ownership.rune.rune_type,
                rune_ownership.rune.effect_value,
                rune_ownership.level,
            )
        )

    selected_skill_ids: set[int] = set()
    for selection in account.skill_selections:
        if selection.equipped_slot is None:
            continue
        selected_skill_ids.add(selection.skill_id)
        _add(skill_effect_contribution(selection.skill))

    recommended_power = (
        account.current_chapter.recommended_combat_power
        if account.current_chapter is not None
        else None
    )

    return BuildContext(
        account_id=account.id,
        hero_level=hero_level,
        attack=totals["attack"],
        defense=totals["defense"],
        max_hp=totals["max_hp"],
        attack_speed=totals["attack_speed"],
        crit_chance=totals["crit_chance"],
        crit_damage=totals["crit_damage"],
        movement_speed=totals["movement_speed"],
        life_steal=totals["life_steal"],
        dodge=totals["dodge"],
        resource_gain=totals["resource_gain"],
        combat_power=account.combat_power,
        recommended_combat_power=recommended_power,
        projectile_count=totals["projectile_count"],
        bounce_count=totals["bounce_count"],
        selected_skill_ids=frozenset(selected_skill_ids),
    )
