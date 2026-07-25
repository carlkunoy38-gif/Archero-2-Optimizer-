"""Shared scoring primitives — the actual "decision engine" every
advisor is built from.

Each function reduces a `BuildContext` to a single number summarizing
one dimension of the build. An advisor combines these differently for
its own purpose (the Skill Advisor weighs them by candidate skill type;
a future Gear Advisor would compare `offense_score`/`defense_score`
across a *hypothetical* `BuildContext` per candidate item; a Farm
Advisor would weigh `utility_score` against chapter energy cost) — but
none of them should recompute "how strong is this build offensively"
themselves. If a new advisor needs a dimension not covered here (e.g. a
Farm Advisor's "expected loot value per energy spent"), add a primitive
here, not inside that advisor's module.

Every function is a pure function of a `BuildContext` — no I/O, no
dependency on anything outside `app.optimizer`.
"""

from __future__ import annotations

import math

from app.optimizer import weights
from app.optimizer.context import BuildContext


def offense_score(context: BuildContext) -> float:
    """Overall damage-output potential: raw attack, scaled up by attack
    speed (more hits) and by the expected crit multiplier."""

    crit_multiplier = 1.0 + context.crit_chance * context.crit_damage
    return context.attack * (1.0 + context.attack_speed) * crit_multiplier


def defense_score(context: BuildContext) -> float:
    """Overall survivability: effective HP, scaled up by flat defense
    (as a percentage damage reduction proxy) and by dodge chance."""

    return context.max_hp * (1.0 + context.defense / 100.0) * (1.0 + context.dodge)


def mobility_score(context: BuildContext) -> float:
    """How well this build avoids damage through positioning rather
    than tanking it: movement speed plus dodge chance."""

    return context.movement_speed + context.dodge


def utility_score(context: BuildContext) -> float:
    """Non-combat efficiency: currently just resource gain, since
    that's the only utility-flavored stat modeled in the catalog today
    (see `StatType` in `app/domain/models/enums.py`)."""

    return context.resource_gain


def aoe_score(context: BuildContext) -> float:
    """Damage-output potential against *multiple* enemies at once —
    extra projectiles and ricochet/bounce hits multiply how much of a
    screen one attack covers, which `offense_score` (single-target DPS)
    does not capture at all. `PROJECTILE_AOE_FACTOR` and
    `BOUNCE_AOE_FACTOR` are deliberately different weights so a
    projectile-count skill and a bounce-count skill of the same tier
    don't come out identical — see `weights.py`.

    Scaled by `sqrt` rather than linearly: the *first* extra projectile
    or bounce covers proportionally more new ground than the fifth
    (there are only so many enemies on screen to hit twice). This is
    also what makes an account's *already-selected* projectile/bounce
    skills (folded into `BuildContext.projectile_count`/`bounce_count`
    by `build_context`) change how much a *new* candidate with the same
    effect is worth — see
    `tests/backend/test_optimizer_skill_advisor.py::test_existing_selected_skill_reduces_marginal_value_of_a_similar_new_one`.
    """

    extra_projectiles = max(0.0, context.projectile_count - 1.0)
    bounce_count = max(0.0, context.bounce_count)
    return context.attack * (
        math.sqrt(extra_projectiles) * weights.PROJECTILE_AOE_FACTOR
        + math.sqrt(bounce_count) * weights.BOUNCE_AOE_FACTOR
    )


def summon_score(context: BuildContext) -> float:
    """Damage output from rune-granted summons/elemental procs (Circle,
    Sprite, Plant, Ice, Poison, Lightning, Fire — see "Module 6" in
    docs/architecture.md for where these `BuildContext` fields came
    from). A build that never invests in any of them scores 0 here
    regardless of how strong its main weapon is; a build that stacks
    several benefits from all of them at once, unlike `aoe_score`'s
    single projectile/bounce mechanic.

    A plain sum, not scaled by `attack` or by `sqrt` like `aoe_score`:
    there is no real-game data yet on whether these procs scale off the
    hero's own attack or are self-contained flat damage, so summing the
    flat bonuses directly is the simplest model that doesn't assume an
    interaction the game data doesn't confirm — see `ObjectiveProfile`'s
    `summon_weight` for how this is scaled relative to the other
    dimensions instead.
    """

    return (
        context.circle_damage
        + context.sprite_damage
        + context.plant_damage
        + context.ice_damage
        + context.poison_damage
        + context.lightning_damage
        + context.fire_damage
    )
