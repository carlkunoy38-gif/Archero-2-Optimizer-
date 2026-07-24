"""ObjectiveProfile: what "good" means for a specific decision.

`engine.py`'s primitives each measure one dimension of a build; an
`ObjectiveProfile` is a named weighting of those dimensions into one
scalar, so "how good is this build" has a different answer for a boss
fight (single-target `offense_score` matters most) than for farming
(`aoe_score`/`utility_score` matter most) than for a build that's
currently under-powered for its chapter (`defense_score`/
`mobility_score` matter most). Advisors compare a build's objective
score *before* and *after* a candidate change — the marginal difference
is the candidate's value for that objective. See
`app.optimizer.simulator.apply_skill` and
`app.optimizer.advisors.skill_advisor.score_skill`.

A plain weighted-sum dataclass rather than a class hierarchy: swapping
"what matters" is a data change (different numbers), not a different
behavior, so there is nothing here that calls for subclassing.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import NotFoundError
from app.optimizer import engine, weights
from app.optimizer.context import BuildContext


@dataclass(frozen=True)
class ObjectiveProfile:
    name: str
    offense_weight: float
    defense_weight: float
    mobility_weight: float
    utility_weight: float
    aoe_weight: float

    def evaluate(self, context: BuildContext) -> float:
        """A single scalar "how good is this build for this objective"
        score. Mobility is weighted more heavily than the profile's base
        weight when the build is under-powered for its current chapter
        — see `weights.UNDERPOWERED_MOBILITY_BOOST` — since that holds
        regardless of which objective is being optimized for."""

        underpowered = max(0.0, 1.0 - context.power_gap_ratio)
        mobility_weight = self.mobility_weight * (
            1.0 + underpowered * weights.UNDERPOWERED_MOBILITY_BOOST
        )
        return (
            engine.offense_score(context) * self.offense_weight
            + engine.defense_score(context) * self.defense_weight
            + engine.mobility_score(context) * mobility_weight
            + engine.utility_score(context) * self.utility_weight
            + engine.aoe_score(context) * self.aoe_weight
        )


def _from_weights(name: str) -> ObjectiveProfile:
    row = weights.OBJECTIVE_WEIGHTS[name]
    return ObjectiveProfile(
        name=name,
        offense_weight=row["offense"],
        defense_weight=row["defense"],
        mobility_weight=row["mobility"],
        utility_weight=row["utility"],
        aoe_weight=row["aoe"],
    )


#: General-purpose default: a reasonable blend of every dimension, used
#: when the caller has no more specific objective in mind.
BALANCED = _from_weights("balanced")

#: Single-target damage matters most; clearing a screen of trash mobs
#: does not.
BOSS = _from_weights("boss")

#: Clearing many enemies per run and resource efficiency matter most;
#: single-target burst does not.
FARM = _from_weights("farm")

#: Survivability matters most — for a build that's struggling to clear
#: its current chapter at all.
SURVIVAL = _from_weights("survival")

BY_NAME: dict[str, ObjectiveProfile] = {
    profile.name: profile for profile in (BALANCED, BOSS, FARM, SURVIVAL)
}


def resolve(name: str) -> ObjectiveProfile:
    """Look up an objective by name, raising `NotFoundError` (a 404 at
    the API layer, same as a missing account or catalog row) for an
    unknown one — every advisor's `advise_for_account` calls this
    instead of indexing `BY_NAME` itself, so the error message and
    behavior for "unknown objective" can't drift between advisors."""

    try:
        return BY_NAME[name]
    except KeyError:
        known = ", ".join(sorted(BY_NAME))
        raise NotFoundError(f"Unknown objective {name!r}; expected one of: {known}") from None
