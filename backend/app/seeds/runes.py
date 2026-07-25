"""Seed the Rune catalog with real rune data sourced from live-game
screenshots (Archero 2, "Rune Workshop" screen).

Run via `database/seeds/seed_runes.py` — see that script and
`database/seeds/README.md` for how, and the ground rule every seed
script follows: populate data purely through the SQLAlchemy models in
`app/domain/models/`, never raw SQL, and stay idempotent (safe to
re-run without creating duplicates).

What's real here versus still a placeholder:
- Every rune's *name* and every flat numeric effect below (Circle/Sprite/
  Plant/Ice/Poison/Lightning/Fire DMG, ATK PWR, Max HP) was read directly
  off account screenshots and matches the account-level aggregate totals
  shown in the same screenshots exactly (e.g. summing "Circle DMG" across
  every seeded rune that grants it reproduces the account's displayed
  total of +30) — this is real data, not an invented example.
- Percentage-based effects (e.g. "Fire DMG +50%", "Main weapon DMG +10%",
  "Circle speed +50%", stat-conversion effects) are recorded only in
  `effect_description` as free text, not as a `RuneEffect` row: this
  project's effect model (`RuneEffect.value`) is a flat additive number
  onto a `BuildContext` field, and there is no percentage-modifier field
  to put a "+50%" figure into without silently misrepresenting it as
  flat. Modeling percentage modifiers properly is future work once the
  engine supports multiplicative effects.
- `rarity` is a GAME DATA PLACEHOLDER: the source screenshots show a
  rarity-like icon per rune but not a readable rarity label, so these are
  a reasonable guess (`RARE` for the four "ATK PWR" runes, `EPIC` for the
  four "Max HP" runes with a distinct icon, `COMMON` for the two plain
  stat runes) rather than a transcription of real data.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import EffectType, Rarity, Rune, RuneEffect, RuneType

#: (name, rune_type, rarity, effect_description, [(effect_type, value), ...])
_RUNES: list[tuple[str, RuneType, Rarity, str | None, list[tuple[EffectType, float]]]] = [
    (
        "Spin SPD Up",
        RuneType.OFFENSE,
        Rarity.RARE,
        "Circle speed +50%",
        [
            (EffectType.CIRCLE_DAMAGE_BONUS, 5.0),
            (EffectType.CIRCLE_DAMAGE_BONUS, 10.0),
            (EffectType.ATTACK_BONUS, 50.0),
        ],
    ),
    (
        "Sharp Arrow",
        RuneType.OFFENSE,
        Rarity.RARE,
        "Main weapon DMG +10%",
        [
            (EffectType.ATTACK_BONUS, 5.0),
            (EffectType.ATTACK_BONUS, 10.0),
            (EffectType.ATTACK_BONUS, 50.0),
        ],
    ),
    (
        "Flamenox Seal",
        RuneType.OFFENSE,
        Rarity.RARE,
        "Fire DMG +50%",
        [
            (EffectType.FIRE_DAMAGE_BONUS, 10.0),
            (EffectType.POISON_DAMAGE_BONUS, 10.0),
            (EffectType.ATTACK_BONUS, 50.0),
        ],
    ),
    (
        "Vine Bind",
        RuneType.OFFENSE,
        Rarity.RARE,
        (
            "When summoned, Plant Guardians link with up to 2 other Plant "
            "Guardians. Links deal 10% ATK as Poison DMG per second and "
            "apply Slow to enemies hit."
        ),
        [
            (EffectType.PLANT_DAMAGE_BONUS, 5.0),
            (EffectType.PLANT_DAMAGE_BONUS, 10.0),
            (EffectType.ATTACK_BONUS, 50.0),
        ],
    ),
    (
        "Flamenox Touch",
        RuneType.DEFENSE,
        Rarity.EPIC,
        "Starting Skill: Ignite a random enemy every 2s",
        [
            (EffectType.POISON_DAMAGE_BONUS, 10.0),
            (EffectType.FIRE_DAMAGE_BONUS, 10.0),
            (EffectType.MAX_HP_BONUS, 200.0),
        ],
    ),
    (
        "Circle",
        RuneType.DEFENSE,
        Rarity.EPIC,
        "Start with 2 weak circling orbs",
        [
            (EffectType.CIRCLE_DAMAGE_BONUS, 5.0),
            (EffectType.CIRCLE_DAMAGE_BONUS, 10.0),
            (EffectType.MAX_HP_BONUS, 200.0),
        ],
    ),
    (
        "Frostshock Touch",
        RuneType.DEFENSE,
        Rarity.EPIC,
        "Starting Skill: Strike a random enemy with lightning every 2s",
        [
            (EffectType.ICE_DAMAGE_BONUS, 10.0),
            (EffectType.LIGHTNING_DAMAGE_BONUS, 10.0),
            (EffectType.MAX_HP_BONUS, 200.0),
        ],
    ),
    (
        "Melee Sprite",
        RuneType.DEFENSE,
        Rarity.EPIC,
        (
            "Start with a Melee Sprite (Melee Sprites and their clones "
            "count as 2 units for Sprite count)"
        ),
        [
            (EffectType.SPRITE_DAMAGE_BONUS, 5.0),
            (EffectType.SPRITE_DAMAGE_BONUS, 10.0),
            (EffectType.MAX_HP_BONUS, 200.0),
        ],
    ),
    (
        "Resilience",
        RuneType.UTILITY,
        Rarity.COMMON,
        "Converts 15% ATK PWR to 20% Max HP",
        [(EffectType.MAX_HP_BONUS, 240.0)],
    ),
    (
        "Intelligence",
        RuneType.UTILITY,
        Rarity.COMMON,
        "EXP gain rate +10%",
        [(EffectType.MAX_HP_BONUS, 240.0)],
    ),
]


def seed_runes(db: Session) -> int:
    """Insert any rune from `_RUNES` not already present by name.

    Idempotent: re-running this against a database that already has some
    or all of these runes only inserts the ones still missing, so it is
    safe to run again after a fresh migration or alongside future seed
    additions.
    """

    existing_names = set(db.scalars(select(Rune.name)).all())
    inserted = 0
    for name, rune_type, rarity, effect_description, effects in _RUNES:
        if name in existing_names:
            continue
        rune = Rune(
            name=name,
            rune_type=rune_type,
            rarity=rarity,
            effect_description=effect_description,
        )
        rune.effects = [
            RuneEffect(effect_type=effect_type, value=value) for effect_type, value in effects
        ]
        db.add(rune)
        inserted += 1
    db.commit()
    return inserted
