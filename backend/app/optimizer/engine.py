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
