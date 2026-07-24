"""Chapter suitability primitives — the engine-adjacent math the
Chapter Advisor is built from, kept separate from `engine.py` because
these are functions of `(BuildContext, Chapter)`, not `BuildContext`
alone, the way every `engine.py` primitive is.

Two different questions need two different formulas, not one formula
reused with different objective weights: "which chapter should I farm
repeatedly" wants somewhere *comfortably* within reach and cheap on
energy; "which chapter should I push into next" wants the *furthest*
chapter that's still safely reachable at all. Both still reuse
`ObjectiveProfile.evaluate` and `BuildContext.power_gap_ratio`'s
same underlying idea (`combat_power` relative to a recommended power),
just applied per-chapter instead of to the account's single current
chapter.
"""

from __future__ import annotations

from app.domain.models import Chapter
from app.optimizer import weights
from app.optimizer.context import BuildContext
from app.optimizer.objectives import ObjectiveProfile


def power_gap_for_chapter(context: BuildContext, chapter: Chapter) -> float:
    """`combat_power / chapter.recommended_combat_power`: <1 means
    under-powered for this specific chapter, >=1 means safely capable
    of it. Mirrors `BuildContext.power_gap_ratio`, just parameterized by
    an arbitrary chapter instead of the account's current one."""

    if not chapter.recommended_combat_power:
        return 1.0
    return context.combat_power / chapter.recommended_combat_power


def clear_safety(gap: float) -> float:
    """0.0 at or below `MIN_SAFE_POWER_GAP_RATIO` (too risky to
    recommend at all), ramping linearly to 1.0 at `gap == 1.0` (at the
    recommended power), capped at 1.0 beyond that — being further
    over-powered doesn't make a chapter "more safe" than already safe."""

    if gap <= weights.MIN_SAFE_POWER_GAP_RATIO:
        return 0.0
    if gap >= 1.0:
        return 1.0
    span = 1.0 - weights.MIN_SAFE_POWER_GAP_RATIO
    return (gap - weights.MIN_SAFE_POWER_GAP_RATIO) / span


def farm_suitability(context: BuildContext, chapter: Chapter, objective: ObjectiveProfile) -> float:
    """How good a repeatable farming target this chapter is: the
    build's objective-weighted strength, scaled down by how unsafe the
    chapter currently is and by its energy cost — a chapter that costs
    more energy per attempt is worth less per unit of grinding time,
    all else equal."""

    gap = power_gap_for_chapter(context, chapter)
    safety = clear_safety(gap)
    build_component = objective.evaluate(context)
    energy_efficiency = 1.0 / max(chapter.energy_cost, 1)
    return build_component * safety * energy_efficiency * weights.FARM_SCORE_SCALE


def progression_suitability(
    context: BuildContext, chapter: Chapter, objective: ObjectiveProfile
) -> float:
    """How good a "push into this next" target this chapter is:
    rewards *further* chapters (higher `recommended_combat_power`), but
    only in proportion to how safely reachable they currently are — an
    unreachable chapter (`clear_safety` 0) scores 0 regardless of how
    far it is, rather than still nominally "the furthest option"."""

    gap = power_gap_for_chapter(context, chapter)
    safety = clear_safety(gap)
    return chapter.recommended_combat_power * safety * weights.PROGRESSION_SCORE_SCALE
