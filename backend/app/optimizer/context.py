"""BuildContext: a pure snapshot of one account's current build,
aggregated from its active hero, equipped gear, socketed runes, and
active pet — the one thing every advisor scores candidates against.

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

from dataclasses import dataclass

from app.domain.models import StatType, UserAccount
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


@dataclass(frozen=True)
class BuildContext:
    """An immutable snapshot of one account's aggregated build stats.

    Every numeric field is a sum across whatever is currently
    active/equipped — not a per-item breakdown. Advisors that need to
    compare *individual* gear options (a future Gear Advisor) work
    differently: they'd build a hypothetical `BuildContext` per
    candidate and compare `engine.py` scores across those, rather than
    reading fields off of one shared context the way the Skill Advisor
    does.
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


def build_context(account: UserAccount) -> BuildContext:
    totals: dict[str, float] = dict.fromkeys(set(_STAT_TYPE_FIELD.values()), 0.0)

    active_hero = next((h for h in account.heroes if h.is_active), None)
    hero_level = active_hero.level if active_hero is not None else 0
    if active_hero is not None:
        factor = _level_multiplier(active_hero.level)
        totals["attack"] += active_hero.hero.base_attack * factor
        totals["defense"] += active_hero.hero.base_defense * factor
        totals["max_hp"] += active_hero.hero.base_hp * factor
        totals["attack_speed"] += active_hero.hero.base_attack_speed

    equipped_weapon = next((w for w in account.weapons if w.is_equipped), None)
    if equipped_weapon is not None:
        factor = _level_multiplier(equipped_weapon.level) * _star_multiplier(
            equipped_weapon.star_level
        )
        totals["attack"] += equipped_weapon.weapon.base_damage * factor
        totals["attack_speed"] += equipped_weapon.weapon.base_attack_speed
        totals["crit_chance"] += equipped_weapon.weapon.crit_chance_bonus

    for armor_ownership in account.armor_pieces:
        if not armor_ownership.is_equipped:
            continue
        factor = _level_multiplier(armor_ownership.level) * _star_multiplier(
            armor_ownership.star_level
        )
        totals["defense"] += armor_ownership.armor.base_defense * factor
        totals["max_hp"] += armor_ownership.armor.base_hp * factor

    for ring_ownership in account.rings:
        if not ring_ownership.is_equipped:
            continue
        field = _STAT_TYPE_FIELD.get(ring_ownership.ring.primary_stat)
        if field is not None:
            totals[field] += ring_ownership.ring.primary_stat_value * _level_multiplier(
                ring_ownership.level
            )

    for amulet_ownership in account.amulets:
        if not amulet_ownership.is_equipped:
            continue
        field = _STAT_TYPE_FIELD.get(amulet_ownership.amulet.primary_stat)
        if field is not None:
            totals[field] += amulet_ownership.amulet.primary_stat_value * _level_multiplier(
                amulet_ownership.level
            )

    active_pet = next((p for p in account.pets if p.is_active), None)
    if active_pet is not None:
        field = _STAT_TYPE_FIELD.get(active_pet.pet.bonus_stat)
        if field is not None:
            totals[field] += active_pet.pet.bonus_stat_value * _level_multiplier(
                active_pet.level
            )

    for rune_ownership in account.runes:
        if not rune_ownership.is_equipped:
            continue
        field = weights.RUNE_TYPE_STAT_FIELD.get(rune_ownership.rune.rune_type)
        if field is not None:
            totals[field] += rune_ownership.rune.effect_value * _level_multiplier(
                rune_ownership.level
            )

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
    )
