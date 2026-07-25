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

# --- Build-context aggregation (app/optimizer/context.py) ------------------

#: Fraction of a base stat added per level above 1 (simple linear
#: growth — a placeholder for a real per-entity growth curve, which
#: isn't modeled anywhere in the catalog yet).
LEVEL_GROWTH_RATE = 0.08

#: Fraction of a weapon/armor's base value added per star level, on top
#: of the level multiplier.
STAR_LEVEL_BONUS = 0.05

# --- Engine primitives (app/optimizer/engine.py) ---------------------------

#: `aoe_score`'s per-extra-projectile and per-bounce multiplier against
#: `attack`. Deliberately different from each other so a
#: `PROJECTILE_COUNT` skill and a `BOUNCE_COUNT` skill of the same
#: catalog tier don't score identically — see "Ricochet vs. Multishot"
#: in docs/architecture.md.
PROJECTILE_AOE_FACTOR = 0.015
BOUNCE_AOE_FACTOR = 0.025

# --- Objective profiles (app/optimizer/objectives.py) -----------------------

#: Per-objective weighting of the four `engine.py` scores plus
#: `aoe_score`, keyed by profile name. What "good" means depends on what
#: the player is actually trying to do right now: a boss fight rewards
#: single-target `offense_score` over `aoe_score`; farming is the
#: opposite. `objectives.py` turns each row into an `ObjectiveProfile`.
OBJECTIVE_WEIGHTS: dict[str, dict[str, float]] = {
    "balanced": {"offense": 0.02, "defense": 0.05, "mobility": 40.0, "utility": 1.5, "aoe": 0.02},
    "boss": {"offense": 0.04, "defense": 0.05, "mobility": 30.0, "utility": 0.5, "aoe": 0.005},
    "farm": {"offense": 0.005, "defense": 0.02, "mobility": 20.0, "utility": 3.0, "aoe": 0.08},
    "survival": {"offense": 0.01, "defense": 0.12, "mobility": 60.0, "utility": 1.0, "aoe": 0.01},
}

#: Extra fractional weight `mobility_score` gets in any objective when
#: the build is under-powered for its current chapter, scaled by
#: `(1 - power_gap_ratio)` floored at 0 (e.g. `1.0` doubles the mobility
#: weight when maximally under-powered). Mobility/survival matters more
#: when you're under-leveled regardless of which objective you're
#: optimizing for.
UNDERPOWERED_MOBILITY_BOOST = 1.0

# --- Skill Advisor (app/optimizer/advisors/skill_advisor.py) ---------------

#: Every candidate skill gets this much value per catalog `tier`, before
#: the build-simulated marginal gain from its `SkillEffect` rows is
#: added — see "The Optimizer Engine (Module 3.1)" in
#: docs/architecture.md for why tier is only the floor, not the whole
#: score, now that skills carry structured effects.
SKILL_TIER_BASE_VALUE = 10.0

# --- Upgrade Advisor (app/optimizer/advisors/upgrade_advisor.py) -----------

#: Gold cost of taking an item from level L to L+1 is
#: `BASE_UPGRADE_COST_PER_LEVEL * L` — cost grows linearly with the
#: item's current level, a common shape for mobile-game upgrade curves.
#: There is no real per-item gold-cost data available (the catalog has
#: no cost column at all), so this is a single global placeholder rather
#: than a claim about any specific item's real cost.
BASE_UPGRADE_COST_PER_LEVEL = 50.0

#: How many levels ahead the Upgrade Advisor considers buying for a
#: single item in one recommendation, even with unlimited gold — caps
#: the affordability search and keeps "spend everything on one item" from
#: producing an unbounded number of levels.
MAX_UPGRADE_LEVELS_CONSIDERED = 10

# --- Chapter Advisor (app/optimizer/chapter_scoring.py) --------------------

#: Below this `power_gap_ratio` (combat_power / chapter's
#: recommended_combat_power), a chapter is considered too risky to
#: recommend at all (`clear_safety` returns 0). Above 1.0 (at or over
#: the recommended power), safety is already maximal — there's no
#: separate "over-powered" bonus.
MIN_SAFE_POWER_GAP_RATIO = 0.7

#: Scales `farm_suitability`'s combined
#: `objective-weighted-build-score * safety * energy-efficiency` into a
#: score of a similar order of magnitude to the other advisors.
FARM_SCORE_SCALE = 50.0

#: Scales `progression_suitability`'s
#: `recommended_combat_power * safety` into a score of a similar order
#: of magnitude to the other advisors.
PROGRESSION_SCORE_SCALE = 0.05
