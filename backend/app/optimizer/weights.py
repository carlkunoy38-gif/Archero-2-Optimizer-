"""Every tunable constant the optimizer engine uses, in one place.

This module exists specifically to satisfy "avoid hardcoded rules
scattered around the project": if a number here needs to change — to
tune balance, or because real Archero 2 data becomes available — this
is the only file that should need editing. No advisor, no context
builder, and no engine primitive should have a bare numeric literal
that isn't a structural constant (a loop bound, an index) — if it's a
game-balance decision, it belongs here, named, with a comment
explaining what it controls.

GAME DATA PLACEHOLDER
----------------------
Every value below is an illustrative starting point, not a balance
number derived from real Archero 2 data — which, as elsewhere in this
project (see the root README's "Game data" section), isn't available.
The *shape* of the model (linear level scaling, tier-based skill
baseline, build-relative synergy bonuses) is a reasonable, defensible
design; the specific numbers are not claims about real game balance.
"""

from __future__ import annotations

from app.domain.models.enums import RuneType

# --- Build-context aggregation (app/optimizer/context.py) ------------------

#: Fraction of a base stat added per level above 1 (simple linear
#: growth — a placeholder for a real per-entity growth curve, which
#: isn't modeled anywhere in the catalog yet).
LEVEL_GROWTH_RATE = 0.08

#: Fraction of a weapon/armor's base value added per star level, on top
#: of the level multiplier.
STAR_LEVEL_BONUS = 0.05

#: Runes are tagged with a broad `RuneType` (offense/defense/utility),
#: not a specific `StatType` the way rings/amulets are — this maps each
#: category to the one `BuildContext` field it feeds into.
RUNE_TYPE_STAT_FIELD: dict[RuneType, str] = {
    RuneType.OFFENSE: "attack",
    RuneType.DEFENSE: "defense",
    RuneType.UTILITY: "resource_gain",
}

# --- Skill Advisor (app/optimizer/advisors/skill_advisor.py) ---------------

#: Every candidate skill gets this much value per catalog `tier`,
#: before any build-specific synergy is added.
SKILL_TIER_BASE_VALUE = 10.0

#: An OFFENSIVE skill's synergy bonus is `offense_score(context) * this`
#: — the stronger your build's current damage output, the more an
#: offensive pick compounds it.
OFFENSIVE_SYNERGY_FACTOR = 0.02

#: A DEFENSIVE skill's synergy bonus scales with how far *below* this
#: baseline the build's current `defense_score` sits — a squishy build
#: gets more value from a defensive pick than an already-tanky one.
DEFENSIVE_SCORE_BASELINE = 500.0
DEFENSIVE_SYNERGY_FACTOR = 0.05

#: A UTILITY skill's synergy bonus is `utility_score(context) * this`.
UTILITY_SYNERGY_FACTOR = 1.5

#: A MOVEMENT skill's synergy bonus scales with how under-powered the
#: build currently is for its chapter (`1 - power_gap_ratio`, floored at
#: 0) — mobility/survival matters more when you're under-leveled.
MOVEMENT_SYNERGY_FACTOR = 40.0
