"""Skill Advisor: given the skill choices Archero 2 offers mid-run,
ranks them for one account's *current* build — never a static tier
list, and never treating every skill of the same `skill_type`/`tier` as
interchangeable.

How a skill is scored (Module 3.1 — see "The Optimizer Engine" in
docs/architecture.md for the full rationale): every skill gets a
baseline from its catalog `tier`, then a *marginal* build-simulation
bonus — `simulator.apply_skill` projects the skill's structured
`SkillEffect` rows onto a copy of the build, `objective.evaluate` scores
the build before and after, and the difference is what the skill is
actually worth for this specific build and objective. This is what lets
two skills of the same type and tier (Multishot's extra projectile
versus Ricochet's bounce) score differently, and lets an account's
*already-equipped* skills (folded into `BuildContext` by
`build_context`) change how much a new candidate is worth.

A skill with no modeled `SkillEffect` rows falls back to tier-only
scoring — the marginal gain is simply zero — which degrades gracefully
rather than crashing, but is honestly weaker intelligence than a skill
with real effect data. See
`tests/backend/test_optimizer_skill_advisor.py::test_same_type_same_tier_skills_can_rank_differently`
for the case this whole module exists to get right.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.domain.models import Skill
from app.optimizer import explanations, objectives, simulator, weights
from app.optimizer.context import BuildContext, build_context
from app.optimizer.objectives import ObjectiveProfile
from app.optimizer.results import AdvisorResult, ScoredOption
from app.services import account_service, catalog_service


def score_skill(
    context: BuildContext, skill: Skill, objective: ObjectiveProfile = objectives.BALANCED
) -> ScoredOption[Skill]:
    """Score one candidate skill against a build and objective. Pure
    function — no I/O — so it's directly unit-testable without a
    database."""

    tier_bonus = weights.SKILL_TIER_BASE_VALUE * skill.tier
    before = objective.evaluate(context)
    simulated = simulator.apply_skill(context, skill)
    after = objective.evaluate(simulated)
    marginal_gain = after - before

    changed = explanations.changed_fields(context, simulated)
    reasons = explanations.build_reasons(
        f"Tier {skill.tier} baseline value: {tier_bonus:.1f}",
        changed,
        objective.name,
        marginal_gain,
    )
    summary = explanations.build_summary(skill.name, changed, objective.name, marginal_gain)

    return ScoredOption(
        option=skill,
        score=tier_bonus + marginal_gain,
        summary=summary,
        reasons=reasons,
    )


def advise(
    context: BuildContext,
    candidates: Sequence[Skill],
    objective: ObjectiveProfile = objectives.BALANCED,
) -> AdvisorResult[Skill]:
    """Rank every candidate for this build and objective, best first.

    Ties (equal score) break on catalog `id` ascending — a deterministic
    tiebreak so the *order candidates were submitted in* never changes
    the recommendation, unlike a plain stable sort on score alone."""

    if not candidates:
        raise ValueError("advise() requires at least one candidate skill")

    scored = [score_skill(context, skill, objective) for skill in candidates]
    scored.sort(key=lambda scored_option: (-scored_option.score, scored_option.option.id))
    return AdvisorResult(ranked=tuple(scored))


def advise_for_account(
    db: Session,
    account_id: int,
    candidate_skill_ids: Sequence[int],
    objective_name: str = "balanced",
) -> AdvisorResult[Skill]:
    """DB-aware entry point: loads the account's build and the candidate
    catalog rows (raising `NotFoundError` for a missing account, skill
    id, or objective name, via the same services the rest of the API
    uses), then delegates to the pure `advise` above.
    """

    account = account_service.get_account_detail(db, account_id)
    context = build_context(account)
    objective = objectives.resolve(objective_name)

    seen: set[int] = set()
    candidates: list[Skill] = []
    for skill_id in candidate_skill_ids:
        if skill_id in seen:
            continue
        seen.add(skill_id)
        candidates.append(catalog_service.get_skill(db, skill_id))

    return advise(context, candidates, objective)
