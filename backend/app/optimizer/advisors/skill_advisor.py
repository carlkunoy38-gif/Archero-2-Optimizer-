"""Skill Advisor: given the skill choices Archero 2 offers mid-run,
ranks them for one account's *current* build — never a static tier
list. The same candidate skills can, and should, rank differently for
two accounts with different gear: see
`tests/backend/test_optimizer_skill_advisor.py::test_same_candidates_rank_differently_for_different_builds`
for exactly that case, which is the actual point of this module.

How a skill is scored: every skill gets a baseline from its catalog
`tier`, then a build-specific synergy bonus determined by its
`skill_type` — an OFFENSIVE skill is worth more the harder your build
already hits (it compounds), a DEFENSIVE skill is worth more the
squishier your build currently is (diminishing-returns logic: you get
more from your first points of survivability than your hundredth), a
UTILITY skill scales with resource gain, and a MOVEMENT skill is worth
more the more under-powered you are for your current chapter. All of
the actual numbers are in `app/optimizer/weights.py` — nothing here is
a hardcoded per-skill-name rule, which means this works for any row in
the `Skill` catalog, present or future, without code changes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.domain.models import Skill, SkillType
from app.optimizer import engine, weights
from app.optimizer.context import BuildContext, build_context
from app.optimizer.results import AdvisorResult, ScoredOption
from app.services import account_service, catalog_service


def score_skill(context: BuildContext, skill: Skill) -> ScoredOption[Skill]:
    """Score one candidate skill against a build. Pure function — no I/O
    — so it's directly unit-testable without a database."""

    reasons: list[str] = [
        f"Tier {skill.tier} baseline value: {weights.SKILL_TIER_BASE_VALUE * skill.tier:.1f}"
    ]
    score = weights.SKILL_TIER_BASE_VALUE * skill.tier

    if skill.skill_type == SkillType.OFFENSIVE:
        offense = engine.offense_score(context)
        bonus = offense * weights.OFFENSIVE_SYNERGY_FACTOR
        reasons.append(
            f"Offensive skill, scaled by your build's offense score ({offense:.1f}): +{bonus:.1f}"
        )
        score += bonus

    elif skill.skill_type == SkillType.DEFENSIVE:
        defense = engine.defense_score(context)
        deficiency = max(0.0, weights.DEFENSIVE_SCORE_BASELINE - defense)
        bonus = deficiency * weights.DEFENSIVE_SYNERGY_FACTOR
        if deficiency > 0:
            reasons.append(
                f"Defensive skill: your build's defense score ({defense:.1f}) is below the "
                f"{weights.DEFENSIVE_SCORE_BASELINE:.0f} baseline, so this covers a real gap: "
                f"+{bonus:.1f}"
            )
        else:
            reasons.append(
                f"Defensive skill: your build's defense score ({defense:.1f}) already covers "
                "the baseline, so this adds little: +0.0"
            )
        score += bonus

    elif skill.skill_type == SkillType.UTILITY:
        utility = engine.utility_score(context)
        bonus = utility * weights.UTILITY_SYNERGY_FACTOR
        reasons.append(
            f"Utility skill, scaled by your build's resource gain ({utility:.1f}): +{bonus:.1f}"
        )
        score += bonus

    elif skill.skill_type == SkillType.MOVEMENT:
        gap = context.power_gap_ratio
        underpowered = max(0.0, 1.0 - gap)
        bonus = underpowered * weights.MOVEMENT_SYNERGY_FACTOR
        if underpowered > 0:
            reasons.append(
                f"Movement skill: you're under-powered for your current chapter "
                f"(power ratio {gap:.2f}), so mobility/survival is worth more right now: "
                f"+{bonus:.1f}"
            )
        else:
            reasons.append(
                f"Movement skill: you're at or above the recommended power for your current "
                f"chapter (power ratio {gap:.2f}), so mobility is less urgent: +0.0"
            )
        score += bonus

    return ScoredOption(option=skill, score=score, reasons=tuple(reasons))


def advise(context: BuildContext, candidates: Sequence[Skill]) -> AdvisorResult[Skill]:
    """Rank every candidate for this build, best first."""

    if not candidates:
        raise ValueError("advise() requires at least one candidate skill")

    scored = [score_skill(context, skill) for skill in candidates]
    scored.sort(key=lambda scored_option: scored_option.score, reverse=True)
    return AdvisorResult(ranked=tuple(scored))


def advise_for_account(
    db: Session, account_id: int, candidate_skill_ids: Sequence[int]
) -> AdvisorResult[Skill]:
    """DB-aware entry point: loads the account's build and the candidate
    catalog rows (raising `NotFoundError` for a missing account or skill
    id, via the same services the rest of the API uses), then delegates
    to the pure `advise` above.
    """

    account = account_service.get_account_detail(db, account_id)
    context = build_context(account)

    seen: set[int] = set()
    candidates: list[Skill] = []
    for skill_id in candidate_skill_ids:
        if skill_id in seen:
            continue
        seen.add(skill_id)
        candidates.append(catalog_service.get_skill(db, skill_id))

    return advise(context, candidates)
