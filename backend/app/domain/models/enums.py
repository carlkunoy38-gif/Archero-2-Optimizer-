"""Shared enumerations for the domain layer.

GAME DATA PLACEHOLDER
----------------------
The exact rarity tiers, hero classes, and item categories in live
Archero 2 are not available to this project. The values below are a
realistic best-effort approximation based on publicly documented game
structure, chosen so the schema and optimizer engine are fully
functional today. When authoritative data is available, update these
enums (and re-run a migration) — application code elsewhere refers to
these members by name, not by raw string, so most call sites will not
need to change.
"""

from __future__ import annotations

import enum


class Rarity(enum.StrEnum):
    """Item/hero rarity tier, common to every equippable entity."""

    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"
    CHAOTIC = "chaotic"


class HeroClass(enum.StrEnum):
    """Broad combat role of a hero, used by the scoring engine."""

    WARRIOR = "warrior"
    MAGE = "mage"
    RANGER = "ranger"
    ASSASSIN = "assassin"
    SUPPORT = "support"


class ArmorSlot(enum.StrEnum):
    """Equipment slot an armor piece occupies."""

    HELMET = "helmet"
    CHEST = "chest"
    GLOVES = "gloves"
    BOOTS = "boots"


class StatType(enum.StrEnum):
    """Primary stat a ring/amulet/rune roll can grant.

    Kept generic (rather than one column per stat) so new stat types can
    be added without a schema migration.
    """

    ATTACK = "attack"
    HEALTH = "health"
    DEFENSE = "defense"
    CRIT_CHANCE = "crit_chance"
    CRIT_DAMAGE = "crit_damage"
    ATTACK_SPEED = "attack_speed"
    MOVEMENT_SPEED = "movement_speed"
    LIFE_STEAL = "life_steal"
    DODGE = "dodge"
    RESOURCE_GAIN = "resource_gain"


class RuneType(enum.StrEnum):
    """Category of a socketable rune."""

    OFFENSE = "offense"
    DEFENSE = "defense"
    UTILITY = "utility"


class SkillType(enum.StrEnum):
    """Category of an in-run skill choice."""

    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"
    UTILITY = "utility"
    MOVEMENT = "movement"


class EffectType(enum.StrEnum):
    """A structured, mechanical effect a skill grants (`SkillEffect.effect_type`).

    This is what lets the Optimizer Engine (`app/optimizer/`) tell two
    same-tier, same-category skills apart — e.g. Multishot
    (``PROJECTILE_COUNT``) versus Ricochet (``BOUNCE_COUNT``) versus
    Attack Up (``ATTACK_SPEED_MULTIPLIER``) — instead of scoring every
    OFFENSIVE skill identically. Kept generic (one row per effect on
    `SkillEffect`, rather than a column per possible effect on `Skill`)
    so a skill can carry more than one effect and a new effect type can
    be introduced without a schema migration touching `Skill` itself.

    Each member maps to exactly one `app.optimizer.context.BuildContext`
    field (`app.optimizer.context._EFFECT_TYPE_FIELD`) that the
    Optimizer Engine's build simulator adds the effect's value onto.

    GAME DATA PLACEHOLDER: this is a realistic-shaped set of mechanical
    levers, not a transcription of Archero 2's actual skill effect data.

    The eight members from ``ATTACK_BONUS`` onward were added once real
    account/rune screenshots showed Archero 2 tracking flat "ATK PWR" /
    "Main Weapon DMG" bonuses and per-summon-type damage (Circle, Sprite,
    Plant, Ice, Poison, Lightning, Fire — one per rune-granted companion
    or elemental proc) as genuinely distinct build dimensions, not a
    single generic "attack" number. ``ATTACK_BONUS`` folds both "ATK PWR"
    and "Main Weapon DMG" into the existing `attack` field, since this
    project's build model treats attack additively rather than
    replicating the real game's separate multiplicative ATK-PWR-vs-flat-
    damage mechanics — a deliberate simplification, not a claim that
    real Archero 2 treats them identically.
    """

    PROJECTILE_COUNT = "projectile_count"
    BOUNCE_COUNT = "bounce_count"
    ATTACK_SPEED_MULTIPLIER = "attack_speed_multiplier"
    CRIT_CHANCE_BONUS = "crit_chance_bonus"
    CRIT_DAMAGE_BONUS = "crit_damage_bonus"
    DEFENSE_BONUS = "defense_bonus"
    MAX_HP_BONUS = "max_hp_bonus"
    DODGE_BONUS = "dodge_bonus"
    MOVEMENT_SPEED_BONUS = "movement_speed_bonus"
    RESOURCE_GAIN_BONUS = "resource_gain_bonus"
    LIFE_STEAL_BONUS = "life_steal_bonus"
    ATTACK_BONUS = "attack_bonus"
    CIRCLE_DAMAGE_BONUS = "circle_damage_bonus"
    SPRITE_DAMAGE_BONUS = "sprite_damage_bonus"
    PLANT_DAMAGE_BONUS = "plant_damage_bonus"
    ICE_DAMAGE_BONUS = "ice_damage_bonus"
    POISON_DAMAGE_BONUS = "poison_damage_bonus"
    LIGHTNING_DAMAGE_BONUS = "lightning_damage_bonus"
    FIRE_DAMAGE_BONUS = "fire_damage_bonus"
